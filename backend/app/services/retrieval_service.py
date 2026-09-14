import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

async def retrieve_relevant_chunks(
    query: str, 
    user_context: User, 
    db: AsyncSession, 
    limit: int = 5,
    department_id: Optional[int] = None,
    category: Optional[str] = None,
    academic_year: Optional[str] = None,
    document_id: Optional[int] = None,
    search_mode: str = "semantic"
) -> List[Dict[str, Any]]:
    """
    Search for semantically relevant document chunks while strictly enforcing
    RBAC and metadata filtering.
    """
    if search_mode == "semantic":
        # 1. Generate embedding for query
        embed_service = get_embedding_service()
        query_embedding = await embed_service.generate_embedding(query)
        
        # 2. Build the query to join chunks with documents for filtering
        stmt = select(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
            Document
        ).join(
            Document, Document.id == DocumentChunk.document_id
        )
    else:
        # Keyword search mode
        from sqlalchemy import null
        stmt = select(
            DocumentChunk,
            null().label("distance"), # Distance isn't meaningful here for ordering
            Document
        ).join(
            Document, Document.id == DocumentChunk.document_id
        ).where(DocumentChunk.chunk_text.ilike(f"%{query}%"))
    
    # 3. Apply strict access controls and context isolation
    if document_id is not None:
        # Isolated Mode: Only search within this specific document
        stmt = stmt.where(Document.id == document_id)
        
        # Security: User must own the document if it's a private one
        if user_context.role != "admin":
            stmt = stmt.where(
                (Document.visibility_scope != "private") | 
                (Document.uploaded_by == user_context.id)
            )
        # Allow searching if status is ready or approved
        stmt = stmt.where(Document.status.in_([DocumentStatusEnum.ready, DocumentStatusEnum.approved]))
    else:
        # Global Search Mode: Exclude private documents and require approved status
        stmt = stmt.where(Document.status == DocumentStatusEnum.approved)
        stmt = stmt.where(Document.visibility_scope != "private")
        
        if user_context.role == "student":
            stmt = stmt.where(Document.visibility_scope == "public")
        elif user_context.role == "faculty":
            stmt = stmt.where(Document.visibility_scope.in_(["public", "internal"]))

    # 4. Apply user-provided metadata filters (only applicable in Global Search)
    if department_id is not None:
        stmt = stmt.where(Document.department_id == department_id)
    if category is not None:
        stmt = stmt.where(Document.category == category)
    if academic_year is not None:
        stmt = stmt.where(Document.academic_year == academic_year)
        
    # 5. Execute search and order by relevance (distance)
    if search_mode == "semantic":
        stmt = stmt.order_by("distance").limit(limit)
    else:
        stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 6. Format results
    retrieved = []
    for chunk, distance, doc in rows:
        retrieved.append({
            "id": chunk.id,
            "chunk_text": chunk.chunk_text,
            "document_title": doc.title,
            "page_number": chunk.page_number,
            "document_id": doc.id,
            "relevance_score": 1.0 - float(distance) if distance is not None else 0.0,
            "metadata": chunk.metadata_json
        })
        
    return retrieved
