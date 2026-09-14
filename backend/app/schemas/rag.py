from pydantic import BaseModel, Field
from typing import List, Optional

class SourceNode(BaseModel):
    document_title: str
    page: int
    relevance_score: float
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None

class RAGRequest(BaseModel):
    query: str
    department_id: Optional[int] = None
    category: Optional[str] = None
    academic_year: Optional[str] = None
    conversation_history: List[dict] = Field(default_factory=list)
    document_id: Optional[int] = None
    context_type: Optional[str] = None
    context_id: Optional[str] = None

class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    grounded: bool
