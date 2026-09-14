import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notice import Notice
from app.models.student_data import StudentAttendance, StudentSubjectMarks, StudentFeeRecord
from app.schemas.rag import RAGRequest, RAGResponse, SourceNode
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.llm_service import get_llm_service
from sqlalchemy.future import select

from app.core.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Constants for RAG tuning
RELEVANCE_THRESHOLD = 0.70

def filter_outdated_versions(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of retrieved chunks, if there are chunks from documents with the same title
    but different versions, only keep chunks from the highest version document.
    Assumes metadata contains 'version' or we just deduplicate by title.
    Since we didn't store 'version' in metadata explicitly, we can filter by keeping the 
    chunk with the highest document_id if titles match (assuming newer = higher id).
    """
    # Group by title to find the highest document_id per title
    latest_doc_ids = {}
    for chunk in chunks:
        title = chunk["document_title"]
        doc_id = chunk["document_id"]
        if title not in latest_doc_ids:
            latest_doc_ids[title] = doc_id
        else:
            if doc_id > latest_doc_ids[title]:
                latest_doc_ids[title] = doc_id
                
    # Filter
    filtered_chunks = [c for c in chunks if c["document_id"] == latest_doc_ids[c["document_title"]]]
    return filtered_chunks

async def answer_question(request: RAGRequest, user_context: User, db: AsyncSession) -> RAGResponse:
    # 1. Retrieve chunks
    raw_chunks = await retrieve_relevant_chunks(
        query=request.query,
        user_context=user_context,
        db=db,
        limit=10,
        department_id=request.department_id,
        category=request.category,
        academic_year=request.academic_year,
        document_id=request.document_id
    )
    
    # 2. Apply threshold
    relevant_chunks = [c for c in raw_chunks if c["relevance_score"] >= RELEVANCE_THRESHOLD]
    
    # 3. Resolve version conflicts
    filtered_chunks = filter_outdated_versions(relevant_chunks)
    
    # Cap to top 5 after filtering
    final_chunks = filtered_chunks[:5]
    
    # 4. Construct grounded prompt
    context_text = ""
    for i, chunk in enumerate(final_chunks):
        context_text += f"\n--- Document {i+1}: {chunk['document_title']} (Page {chunk['page_number']}) ---\n"
        context_text += chunk["chunk_text"] + "\n"
        
    user_prompt = f"Context:\n{context_text}\n\nUser Question: {request.query}"
    
    # 4.b. Append specific portal context if requested
    if request.context_type:
        portal_context = ""
        if request.context_type.lower() == "notice" and request.context_id:
            try:
                notice_id = int(request.context_id)
                stmt = select(Notice).where(Notice.id == notice_id)
                res = await db.execute(stmt)
                notice = res.scalars().first()
                if notice:
                    portal_context += f"\n--- SELECTED NOTICE: {notice.title} ---\n{notice.content}\n"
            except ValueError:
                pass
        
        elif request.context_type.lower() == "attendance":
            stmt = select(StudentAttendance).where(StudentAttendance.user_id == user_context.id)
            res = await db.execute(stmt)
            records = res.scalars().all()
            if records:
                portal_context += "\n--- YOUR ATTENDANCE RECORDS ---\n"
                for r in records:
                    portal_context += f"Subject: {r.subject_name} | Percentage: {r.percentage}% | Attended: {r.attended_classes}/{r.total_classes}\n"
            else:
                portal_context += "\n--- YOUR ATTENDANCE RECORDS ---\nNo attendance records found.\n"
                
        elif request.context_type.lower() == "marks":
            stmt = select(StudentSubjectMarks).where(StudentSubjectMarks.user_id == user_context.id)
            res = await db.execute(stmt)
            records = res.scalars().all()
            if records:
                portal_context += "\n--- YOUR MARKS / RESULTS ---\n"
                for r in records:
                    portal_context += f"Subject: {r.subject_name} | Marks: {r.marks_obtained}/{r.total_marks} | Grade: {r.grade}\n"
            else:
                portal_context += "\n--- YOUR MARKS / RESULTS ---\nNo marks records found.\n"

        elif request.context_type.lower() == "fees":
            stmt = select(StudentFeeRecord).where(StudentFeeRecord.user_id == user_context.id)
            res = await db.execute(stmt)
            records = res.scalars().all()
            if records:
                portal_context += "\n--- YOUR FEE RECORDS ---\n"
                for r in records:
                    portal_context += f"Semester: {r.semester} | Total Fee: {r.total_fee} | Paid: {r.paid_fee} | Pending: {r.pending_fee}\n"
            else:
                portal_context += "\n--- YOUR FEE RECORDS ---\nNo fee records found.\n"
                
        if portal_context:
            user_prompt = f"Additional Specific Context for the user's query:\n{portal_context}\n\n" + user_prompt
    
    if not final_chunks:
        # Flag for mock LLM to know context is empty
        user_prompt += " EMPTY_CONTEXT_FLAG"
        
    # 5. Query LLM
    llm_service = get_llm_service()
    answer, grounded = await llm_service.generate_response(
        system_prompt=SYSTEM_PROMPT, 
        user_prompt=user_prompt,
        conversation_history=request.conversation_history
    )
    
    # 6. Format sources
    sources = []
    if grounded:
        for chunk in final_chunks:
            sources.append(SourceNode(
                document_title=chunk["document_title"],
                page=chunk["page_number"],
                relevance_score=round(chunk["relevance_score"], 4),
                document_id=chunk["document_id"],
                chunk_id=chunk.get("id") # Assuming 'id' is chunk_id
            ))
            
    return RAGResponse(
        answer=answer,
        sources=sources,
        grounded=grounded
    )
