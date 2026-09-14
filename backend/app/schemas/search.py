from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SearchResult(BaseModel):
    id: int
    chunk_text: str
    document_title: str
    page_number: int
    document_id: int
    relevance_score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_found: int
