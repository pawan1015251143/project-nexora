from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from sqlalchemy import Enum as SQLEnum
from app.db.database import Base


class ImportStatusEnum(str, enum.Enum):
    new = "new"
    imported = "imported"
    processing = "processing"
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    published = "published"


class NoticeImport(Base):
    """Tracks the complete lifecycle of a notice from demo source to published portal notice."""
    __tablename__ = "notice_imports"

    id = Column(Integer, primary_key=True, index=True)
    source_message_id = Column(Integer, ForeignKey("demo_source_messages.id"), nullable=False, index=True)
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=True)  # Set when published
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Set when indexed to RAG

    status = Column(SQLEnum(ImportStatusEnum), default=ImportStatusEnum.new, index=True)

    # AI-extracted structured data (stored as JSON)
    ai_extracted_json = Column(JSONB, nullable=True)

    # Admin-editable draft fields
    draft_title = Column(String, nullable=True)
    draft_content = Column(Text, nullable=True)
    draft_notice_type = Column(String, nullable=True)

    # Error tracking
    processing_error = Column(Text, nullable=True)

    # Timestamps for each stage
    imported_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Who performed admin actions
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_message = relationship("DemoSourceMessage")
    notice = relationship("Notice")
    document = relationship("Document")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
