"""
Admin Notice Inbox API
All endpoints require admin role.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.models.demo_source_message import DemoSourceMessage
from app.models.notice_import import NoticeImport, ImportStatusEnum
from app.schemas.notice_inbox import (
    DemoSourceMessageResponse,
    NoticeImportResponse,
    NoticeInboxItemResponse,
    ApproveRequest,
    RejectRequest,
    UpdateDraftRequest,
)
from app.services import notice_import_service as svc

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[NoticeInboxItemResponse])
async def list_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """List all demo source messages with their import status."""
    result = await db.execute(
        select(DemoSourceMessage).order_by(DemoSourceMessage.timestamp.desc())
    )
    messages = result.scalars().all()

    items = []
    for msg in messages:
        # Find associated import record
        imp_result = await db.execute(
            select(NoticeImport).where(NoticeImport.source_message_id == msg.id)
        )
        imp = imp_result.scalars().first()

        items.append(NoticeInboxItemResponse(
            source=DemoSourceMessageResponse.model_validate(msg),
            import_record=NoticeImportResponse.model_validate(imp) if imp else None
        ))

    return items


@router.get("/{msg_id}", response_model=NoticeInboxItemResponse)
async def get_inbox_item(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get details of a specific demo source message."""
    result = await db.execute(
        select(DemoSourceMessage).where(DemoSourceMessage.id == msg_id)
    )
    msg = result.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Demo source message not found")

    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()

    return NoticeInboxItemResponse(
        source=DemoSourceMessageResponse.model_validate(msg),
        import_record=NoticeImportResponse.model_validate(imp) if imp else None
    )


@router.get("/{msg_id}/status")
async def get_status(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get current pipeline status for a message."""
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()

    if not imp:
        return {"status": "new", "import_id": None}

    return {
        "status": imp.status,
        "import_id": imp.id,
        "notice_id": imp.notice_id,
        "processing_error": imp.processing_error,
    }


@router.post("/{msg_id}/import", response_model=NoticeImportResponse, status_code=status.HTTP_201_CREATED)
async def import_message(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Import a demo source message into Nexora. Detects duplicates."""
    try:
        ni = await svc.import_message(msg_id, current_user, db)
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        err_str = str(e)
        if "DUPLICATE" in err_str:
            raise HTTPException(status_code=409, detail=err_str)
        raise HTTPException(status_code=404, detail=err_str)


@router.post("/{msg_id}/process", response_model=NoticeImportResponse)
async def process_with_ai(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Run AI processing on an imported message to extract structured fields."""
    # Find import record for this source message
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()
    if not imp:
        raise HTTPException(status_code=404, detail="No import record found. Import the message first.")

    try:
        ni = await svc.process_with_ai(imp.id, current_user, db)
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.patch("/{msg_id}/draft", response_model=NoticeImportResponse)
async def update_draft(
    msg_id: int,
    body: UpdateDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Allow admin to edit the draft before approving."""
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()
    if not imp:
        raise HTTPException(status_code=404, detail="No import record found.")

    try:
        ni = await svc.update_draft(
            imp.id, current_user, db,
            title=body.title,
            content=body.content,
            notice_type=body.notice_type
        )
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{msg_id}/approve", response_model=NoticeImportResponse)
async def approve_import(
    msg_id: int,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Approve an import draft. Creates the Notice record."""
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()
    if not imp:
        raise HTTPException(status_code=404, detail="No import record found.")

    try:
        ni = await svc.approve_import(
            imp.id, current_user, db,
            title=body.title,
            content=body.content,
            priority=body.priority or 0
        )
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{msg_id}/reject", response_model=NoticeImportResponse)
async def reject_import(
    msg_id: int,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Reject an import. Rejected notices are never published to students."""
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()
    if not imp:
        raise HTTPException(status_code=404, detail="No import record found.")

    try:
        ni = await svc.reject_import(imp.id, current_user, db, reason=body.reason)
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{msg_id}/publish", response_model=NoticeImportResponse)
async def publish_notice(
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Publish an approved notice to the college portal and index for RAG."""
    imp_result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == msg_id)
    )
    imp = imp_result.scalars().first()
    if not imp:
        raise HTTPException(status_code=404, detail="No import record found.")

    try:
        ni = await svc.publish_notice(imp.id, current_user, db)
        return NoticeImportResponse.model_validate(ni)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
