from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRoleEnum
from app.models.message_source import MessageSource
from app.models.feedback import Feedback
from app.api.deps import get_current_active_user
from app.schemas.chat import ChatRequest, ChatResponse, FeedbackRequest
from app.schemas.rag import RAGRequest
from app.services.rag_service import answer_question

router = APIRouter()

@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch or Create Conversation
    if request.conversation_id:
        stmt = select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).options(selectinload(Conversation.messages))
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.query[:50] + ("..." if len(request.query) > 50 else ""),
            document_id=request.document_id
        )
        db.add(conversation)
        await db.flush() # Get conversation.id
        
        # Need to ensure messages list exists
        conversation.messages = []

    # 2. Build conversation history
    history = []
    # Only send last 10 messages to avoid token bloat
    for msg in conversation.messages[-10:]:
        history.append({"role": msg.role.value, "content": msg.content})
        
    # 3. Save User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRoleEnum.user,
        content=request.query
    )
    db.add(user_msg)
    await db.flush()

    # 4. Call RAG Service
    rag_request = RAGRequest(
        query=request.query,
        department_id=request.department_id,
        category=request.category,
        academic_year=request.academic_year,
        conversation_history=history,
        document_id=conversation.document_id,
        context_type=request.context_type,
        context_id=request.context_id
    )
    
    try:
        rag_response = await answer_question(rag_request, current_user, db)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unhandled exception in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request. Please try again later.")
        
    # 5. Save Assistant Message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role=MessageRoleEnum.assistant,
        content=rag_response.answer
    )
    db.add(assistant_msg)
    await db.flush()
    
    # 6. Save Sources
    if rag_response.grounded:
        for source in rag_response.sources:
            if source.document_id and source.chunk_id:
                msg_source = MessageSource(
                    message_id=assistant_msg.id,
                    document_id=source.document_id,
                    chunk_id=source.chunk_id,
                    relevance_score=source.relevance_score
                )
                db.add(msg_source)
                
    await db.commit()
    
    # 7. Return
    return ChatResponse(
        answer=rag_response.answer,
        sources=rag_response.sources,
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        grounded=rag_response.grounded
    )

@router.post("/{message_id}/feedback")
async def submit_feedback(
    message_id: int,
    request: FeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify message belongs to user
    stmt = select(Message).join(Conversation).where(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    if message.role != MessageRoleEnum.assistant:
        raise HTTPException(status_code=400, detail="Can only feedback on assistant messages")
        
    # Check existing feedback
    stmt = select(Feedback).where(Feedback.message_id == message_id)
    result = await db.execute(stmt)
    feedback = result.scalar_one_or_none()
    
    if feedback:
        feedback.rating = request.is_helpful
        feedback.comment = request.feedback_text
    else:
        feedback = Feedback(
            message_id=message_id,
            user_id=current_user.id,
            rating=request.is_helpful,
            comment=request.feedback_text
        )
        db.add(feedback)
        
    await db.commit()
    return {"status": "success"}
