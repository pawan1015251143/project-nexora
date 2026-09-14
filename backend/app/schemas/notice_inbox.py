from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class DemoSourceMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_message_id: str
    group_name: str
    sender: str
    message_text: str
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    attachment_content: Optional[str] = None
    timestamp: datetime
    imported: bool
    content_hash: str
    created_at: Optional[datetime] = None


class NoticeImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_message_id: int
    notice_id: Optional[int] = None
    document_id: Optional[int] = None
    status: str
    ai_extracted_json: Optional[dict] = None
    draft_title: Optional[str] = None
    draft_content: Optional[str] = None
    draft_notice_type: Optional[str] = None
    processing_error: Optional[str] = None
    imported_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class NoticeInboxItemResponse(BaseModel):
    """Combined view of a demo source message with its import record."""
    model_config = ConfigDict(from_attributes=True)

    source: DemoSourceMessageResponse
    import_record: Optional[NoticeImportResponse] = None


class ApproveRequest(BaseModel):
    """Optional fields the admin can override before approving."""
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
    priority: Optional[int] = 0


class RejectRequest(BaseModel):
    reason: Optional[str] = None


class UpdateDraftRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
