from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.document import DocumentStatusEnum

class DocumentBase(BaseModel):
    title: str
    category: Optional[str] = None
    department_id: Optional[int] = None
    academic_year: Optional[str] = None
    visibility_scope: str = "public"
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    department_id: Optional[int] = None
    academic_year: Optional[str] = None
    visibility_scope: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    mime_type: str
    file_size: int
    version: int
    status: DocumentStatusEnum
    uploaded_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
