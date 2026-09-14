from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.schemas.search import SearchResponse
from app.api import deps
from app.services.retrieval_service import retrieve_relevant_chunks

router = APIRouter(tags=["search"])

@router.get("", response_model=SearchResponse)
async def search_documents(
    query: str,
    search_mode: str = Query("semantic", description="Must be 'semantic' or 'keyword'"),
    department_id: Optional[int] = None,
    category: Optional[str] = None,
    academic_year: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if search_mode not in ["semantic", "keyword"]:
        search_mode = "semantic"
        
    chunks = await retrieve_relevant_chunks(
        query=query,
        user_context=current_user,
        db=db,
        limit=limit,
        department_id=department_id,
        category=category,
        academic_year=academic_year,
        search_mode=search_mode
    )
    
    return SearchResponse(
        results=chunks,
        total_found=len(chunks)
    )
