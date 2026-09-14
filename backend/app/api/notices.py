from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.models.notice import Notice
from app.models.notice_translation import NoticeTranslation
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.api import deps
from app.services.llm_service import get_llm_service

router = APIRouter(tags=["notices"])

@router.get("", response_model=List[NoticeResponse])
async def list_notices(
    department_id: Optional[int] = None,
    search_query: Optional[str] = None,
    include_expired: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    query = select(Notice)
    
    if department_id:
        query = query.where(Notice.department_id == department_id)
        
    if search_query:
        query = query.where(Notice.title.ilike(f"%{search_query}%") | Notice.content.ilike(f"%{search_query}%"))
        
    if not include_expired and current_user.role != "admin":
        # Students shouldn't see expired notices. Admins might want to if include_expired is True
        from sqlalchemy import or_
        query = query.where(
            or_(Notice.expires_at == None, Notice.expires_at > datetime.utcnow())
        )
        
    # Priority DESC, then published_at DESC
    query = query.order_by(Notice.priority.desc(), Notice.published_at.desc())
    
    result = await db.execute(query)
    notices = result.scalars().all()
    return notices

@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(
    notice_in: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    new_notice = Notice(
        title=notice_in.title,
        content=notice_in.content,
        department_id=notice_in.department_id,
        priority=notice_in.priority,
        expires_at=notice_in.expires_at,
        created_by=current_user.id
    )
    
    db.add(new_notice)
    await db.commit()
    await db.refresh(new_notice)
    return new_notice

@router.put("/{id}", response_model=NoticeResponse)
async def update_notice(
    id: int,
    notice_in: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    result = await db.execute(select(Notice).where(Notice.id == id))
    notice = result.scalars().first()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
        
    update_data = notice_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notice, field, value)
        
    await db.commit()
    await db.refresh(notice)
    return notice

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notice(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    result = await db.execute(select(Notice).where(Notice.id == id))
    notice = result.scalars().first()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
        
    db.delete(notice)
    await db.commit()
    return None

@router.get("/{id}/translation")
async def get_notice_translation(
    id: int,
    mode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if mode not in ["hi_annotated", "hi_full"]:
        raise HTTPException(status_code=400, detail="Invalid translation mode")

    result = await db.execute(select(Notice).where(Notice.id == id))
    notice = result.scalars().first()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
        
    if current_user.role != "admin" and notice.expires_at and notice.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Notice has expired")
        
    trans_result = await db.execute(
        select(NoticeTranslation)
        .where(NoticeTranslation.notice_id == id)
        .where(NoticeTranslation.mode == mode)
    )
    translation = trans_result.scalars().first()
    
    if translation and translation.updated_at >= notice.updated_at:
        return {"content": translation.content}
        
    llm = get_llm_service()
    try:
        new_content = await llm.translate_notice(notice.content, mode)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    if translation:
        translation.content = new_content
        translation.updated_at = datetime.utcnow()
    else:
        translation = NoticeTranslation(
            notice_id=id,
            mode=mode,
            content=new_content,
            updated_at=datetime.utcnow()
        )
        db.add(translation)
        
    await db.commit()
    
    return {"content": new_content}
