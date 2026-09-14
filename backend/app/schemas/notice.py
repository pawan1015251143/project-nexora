from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NoticeBase(BaseModel):
    title: str
    content: str
    department_id: Optional[int] = None
    priority: int = 0
    expires_at: Optional[datetime] = None

class NoticeCreate(NoticeBase):
    pass

class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    department_id: Optional[int] = None
    priority: Optional[int] = None
    expires_at: Optional[datetime] = None

class NoticeResponse(NoticeBase):
    id: int
    published_at: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
