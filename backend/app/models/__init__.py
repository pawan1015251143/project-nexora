from app.db.database import Base
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.notice import Notice
from app.models.notice_translation import NoticeTranslation
from app.models.conversation import Conversation
from app.models.message import Message, MessageRoleEnum
from app.models.message_source import MessageSource
from app.models.feedback import Feedback
from app.models.audit_log import AuditLog
from app.models.student_data import StudentAttendance, StudentSubjectMarks, StudentFeeRecord
from app.models.demo_source_message import DemoSourceMessage
from app.models.notice_import import NoticeImport, ImportStatusEnum

# For SQLAlchemy migrations
__all__ = [
    "User",
    "RoleEnum",
    "Department",
    "Document",
    "DocumentChunk",
    "Notice",
    "NoticeTranslation",
    "Conversation",
    "Message",
    "MessageRoleEnum",
    "MessageSource",
    "Feedback",
    "AuditLog",
    "StudentAttendance",
    "StudentSubjectMarks",
    "StudentFeeRecord",
    "DemoSourceMessage",
    "NoticeImport",
    "ImportStatusEnum",
]
