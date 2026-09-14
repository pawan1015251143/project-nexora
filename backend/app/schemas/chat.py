from pydantic import BaseModel
from typing import List, Optional
from app.schemas.rag import SourceNode

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    department_id: Optional[int] = None
    category: Optional[str] = None
    academic_year: Optional[str] = None
    document_id: Optional[int] = None
    context_type: Optional[str] = None
    context_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    conversation_id: int
    message_id: int
    grounded: bool

class FeedbackRequest(BaseModel):
    is_helpful: bool
    feedback_text: Optional[str] = None
