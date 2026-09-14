from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.db.database import Base


class DemoSourceMessage(Base):
    """Simulates a message received from the ABC College WhatsApp group demo source."""
    __tablename__ = "demo_source_messages"

    id = Column(Integer, primary_key=True, index=True)
    source_message_id = Column(String, unique=True, nullable=False, index=True)  # Unique ID for dedup
    group_name = Column(String, nullable=False, default="ABC College — Official Notices")
    sender = Column(String, nullable=False)
    message_text = Column(Text, nullable=False)
    attachment_name = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True)  # pdf, image, text
    attachment_content = Column(Text, nullable=True)  # simulated extracted text
    timestamp = Column(DateTime, nullable=False)
    imported = Column(Boolean, default=False)
    content_hash = Column(String, nullable=False, index=True)  # SHA256 of message_text for dedup
    created_at = Column(DateTime, default=datetime.utcnow)
