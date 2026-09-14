"""
Notice Import Service
Handles the full lifecycle: Demo Source → Import → AI Processing → Approval → Publish → RAG Index
"""
import hashlib
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.demo_source_message import DemoSourceMessage
from app.models.notice_import import NoticeImport, ImportStatusEnum
from app.models.notice import Notice
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.llm_service import get_llm_service
from app.services.document_processor import chunk_pages_data

logger = logging.getLogger(__name__)


def compute_content_hash(message_text: str, attachment_name: Optional[str] = None) -> str:
    """Compute a SHA-256 fingerprint for duplicate detection."""
    raw = message_text.strip()
    if attachment_name:
        raw += f"|{attachment_name}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def log_audit(db: AsyncSession, user_id: int, action: str, entity_id: int, details: dict):
    """Helper to write an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type="notice_import",
        entity_id=entity_id,
        details_json=details
    )
    db.add(log)


async def import_message(
    source_message_id: int,
    admin_user: User,
    db: AsyncSession
) -> NoticeImport:
    """
    Import a DemoSourceMessage into Nexora.
    Performs duplicate detection by checking if any NoticeImport already references this source.
    """
    # Fetch source message
    result = await db.execute(
        select(DemoSourceMessage).where(DemoSourceMessage.id == source_message_id)
    )
    msg = result.scalars().first()
    if not msg:
        raise ValueError(f"Source message {source_message_id} not found.")

    # Check if already imported (same source_message_id)
    result = await db.execute(
        select(NoticeImport).where(NoticeImport.source_message_id == source_message_id)
    )
    existing = result.scalars().first()
    if existing:
        raise ValueError(f"DUPLICATE: This notice has already been imported. Import ID: {existing.id}")

    # Mark source as imported
    msg.imported = True

    # Create import record
    ni = NoticeImport(
        source_message_id=source_message_id,
        status=ImportStatusEnum.imported,
        imported_at=datetime.utcnow(),
        created_by=admin_user.id
    )
    db.add(ni)
    await db.flush()

    await log_audit(db, admin_user.id, "notice_imported", ni.id, {
        "source_message_id": source_message_id,
        "sender": msg.sender
    })

    await db.commit()
    await db.refresh(ni)
    return ni


async def process_with_ai(
    import_id: int,
    admin_user: User,
    db: AsyncSession
) -> NoticeImport:
    """
    Run AI extraction on the source message.
    Extracts structured fields: title, summary, notice_type, department, etc.
    """
    result = await db.execute(select(NoticeImport).where(NoticeImport.id == import_id))
    ni = result.scalars().first()
    if not ni:
        raise ValueError(f"Import record {import_id} not found.")

    if ni.status not in [ImportStatusEnum.imported, ImportStatusEnum.draft]:
        raise ValueError(f"Cannot process: current status is {ni.status}")

    # Fetch source message
    result = await db.execute(
        select(DemoSourceMessage).where(DemoSourceMessage.id == ni.source_message_id)
    )
    msg = result.scalars().first()

    ni.status = ImportStatusEnum.processing
    await db.commit()

    try:
        llm = get_llm_service()
        extracted = await llm.extract_notice_info(
            message_text=msg.message_text,
            attachment_content=msg.attachment_content or ""
        )

        ni.ai_extracted_json = extracted
        ni.draft_title = extracted.get("title", "")
        ni.draft_content = _build_draft_content(msg, extracted)
        ni.draft_notice_type = extracted.get("notice_type", "General")
        ni.status = ImportStatusEnum.draft
        ni.processed_at = datetime.utcnow()
        ni.processing_error = None

        await log_audit(db, admin_user.id, "notice_processed", ni.id, {
            "notice_type": extracted.get("notice_type"),
            "title": extracted.get("title")
        })

    except RuntimeError as e:
        ni.status = ImportStatusEnum.imported  # Revert to imported so retry is possible
        ni.processing_error = str(e)
        logger.error(f"AI processing failed for import {import_id}: {e}")

    await db.commit()
    await db.refresh(ni)
    return ni


def _build_draft_content(msg: DemoSourceMessage, extracted: dict) -> str:
    """Build the draft notice content from AI extraction + original source."""
    lines = []

    if extracted.get("summary"):
        lines.append(extracted["summary"])
        lines.append("")

    if extracted.get("instructions"):
        lines.append("Instructions:")
        lines.append(extracted["instructions"])
        lines.append("")

    if extracted.get("deadline"):
        lines.append(f"Deadline: {extracted['deadline']}")
        lines.append("")

    if extracted.get("important_dates"):
        lines.append("Important Dates:")
        for d in extracted["important_dates"]:
            lines.append(f"  - {d}")
        lines.append("")

    if extracted.get("contact_info"):
        lines.append(f"Contact: {extracted['contact_info']}")
        lines.append("")

    lines.append("---")
    lines.append(f"Source: {msg.group_name} | Sender: {msg.sender}")

    return "\n".join(lines)


async def update_draft(
    import_id: int,
    admin_user: User,
    db: AsyncSession,
    title: Optional[str] = None,
    content: Optional[str] = None,
    notice_type: Optional[str] = None
) -> NoticeImport:
    """Allow admin to edit draft before approval."""
    result = await db.execute(select(NoticeImport).where(NoticeImport.id == import_id))
    ni = result.scalars().first()
    if not ni:
        raise ValueError(f"Import record {import_id} not found.")

    if ni.status not in [ImportStatusEnum.draft, ImportStatusEnum.pending_approval]:
        raise ValueError(f"Cannot edit draft in status: {ni.status}")

    if title is not None:
        ni.draft_title = title
    if content is not None:
        ni.draft_content = content
    if notice_type is not None:
        ni.draft_notice_type = notice_type

    await db.commit()
    await db.refresh(ni)
    return ni


async def approve_import(
    import_id: int,
    admin_user: User,
    db: AsyncSession,
    title: Optional[str] = None,
    content: Optional[str] = None,
    priority: int = 0
) -> NoticeImport:
    """
    Approve the import. Creates the Notice record but doesn't publish yet.
    """
    result = await db.execute(select(NoticeImport).where(NoticeImport.id == import_id))
    ni = result.scalars().first()
    if not ni:
        raise ValueError(f"Import record {import_id} not found.")

    if ni.status not in [ImportStatusEnum.draft, ImportStatusEnum.imported, ImportStatusEnum.pending_approval]:
        raise ValueError(f"Cannot approve: current status is {ni.status}")

    # Fetch source message for context
    result = await db.execute(
        select(DemoSourceMessage).where(DemoSourceMessage.id == ni.source_message_id)
    )
    msg = result.scalars().first()

    # Use admin-provided or AI-extracted values
    final_title = title or ni.draft_title or f"Notice from {msg.sender}"
    final_content = content or ni.draft_content or msg.message_text

    ni.status = ImportStatusEnum.approved
    ni.approved_at = datetime.utcnow()
    ni.reviewed_by = admin_user.id

    # Override draft with final values
    ni.draft_title = final_title
    ni.draft_content = final_content

    await log_audit(db, admin_user.id, "notice_approved", ni.id, {
        "title": final_title
    })

    await db.commit()
    await db.refresh(ni)
    return ni


async def reject_import(
    import_id: int,
    admin_user: User,
    db: AsyncSession,
    reason: Optional[str] = None
) -> NoticeImport:
    """Reject the import. Notice will NOT be published."""
    result = await db.execute(select(NoticeImport).where(NoticeImport.id == import_id))
    ni = result.scalars().first()
    if not ni:
        raise ValueError(f"Import record {import_id} not found.")

    if ni.status in [ImportStatusEnum.published, ImportStatusEnum.rejected]:
        raise ValueError(f"Cannot reject: current status is {ni.status}")

    ni.status = ImportStatusEnum.rejected
    ni.rejected_at = datetime.utcnow()
    ni.reviewed_by = admin_user.id
    if reason:
        ni.processing_error = f"Rejected: {reason}"

    await log_audit(db, admin_user.id, "notice_rejected", ni.id, {
        "reason": reason
    })

    await db.commit()
    await db.refresh(ni)
    return ni


async def publish_notice(
    import_id: int,
    admin_user: User,
    db: AsyncSession
) -> NoticeImport:
    """
    Publish the approved notice:
    1. Create Notice record in existing notice system
    2. Index notice text as Document + DocumentChunks for RAG
    3. Mark import as published
    """
    result = await db.execute(select(NoticeImport).where(NoticeImport.id == import_id))
    ni = result.scalars().first()
    if not ni:
        raise ValueError(f"Import record {import_id} not found.")

    if ni.status != ImportStatusEnum.approved:
        raise ValueError(f"Cannot publish: must be approved first. Current status: {ni.status}")

    # Fetch source message
    result = await db.execute(
        select(DemoSourceMessage).where(DemoSourceMessage.id == ni.source_message_id)
    )
    msg = result.scalars().first()

    title = ni.draft_title or f"Notice from {msg.sender}"
    content = ni.draft_content or msg.message_text

    # 1. Create Notice in existing portal
    notice = Notice(
        title=title,
        content=content,
        priority=0,
        published_at=datetime.utcnow(),
        created_by=admin_user.id
    )
    db.add(notice)
    await db.flush()

    # 2. Index to RAG as a virtual Document
    # Store notice text as a temporary file approach using in-memory chunking
    await _index_notice_to_rag(notice, msg, content, admin_user, db)

    # 3. Update import record
    ni.notice_id = notice.id
    ni.status = ImportStatusEnum.published
    ni.published_at = datetime.utcnow()

    await log_audit(db, admin_user.id, "notice_published", ni.id, {
        "notice_id": notice.id,
        "title": title
    })

    await db.commit()
    await db.refresh(ni)
    return ni


async def _index_notice_to_rag(
    notice: Notice,
    msg: DemoSourceMessage,
    content: str,
    admin_user: User,
    db: AsyncSession
):
    """
    Create a virtual Document and DocumentChunks for the notice so it's
    searchable via the existing RAG/vector pipeline.
    """
    try:
        # Create a virtual Document record (no physical file needed)
        virtual_doc = Document(
            title=notice.title,
            file_path=f"virtual://notice/{notice.id}",  # Virtual path marker
            mime_type="text/plain",
            file_size=len(content.encode("utf-8")),
            category="Notice",
            visibility_scope="public",
            status=DocumentStatusEnum.ready,
            uploaded_by=admin_user.id,
        )
        db.add(virtual_doc)
        await db.flush()

        # Update import to link document
        result = await db.execute(
            select(NoticeImport).where(NoticeImport.notice_id == notice.id)
        )
        ni = result.scalars().first()
        if ni:
            ni.document_id = virtual_doc.id

        # Build pages_data from content
        pages_data = [{"page_number": 1, "text": content}]

        # Also include attachment content as page 2 if available
        if msg.attachment_content:
            pages_data.append({"page_number": 2, "text": msg.attachment_content})

        metadata_base = {
            "document_id": virtual_doc.id,
            "source_title": notice.title,
            "category": "Notice",
            "visibility_scope": "public",
        }

        chunks = await chunk_pages_data(pages_data, metadata_base)

        # Update chunk document_id references
        for chunk in chunks:
            chunk.document_id = virtual_doc.id

        db.add_all(chunks)
        logger.info(f"Indexed notice '{notice.title}' as {len(chunks)} chunks for RAG.")

    except Exception as e:
        logger.error(f"Failed to index notice to RAG: {e}")
        # Don't fail the publish — the notice is still created, just won't be in RAG
