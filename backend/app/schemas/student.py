from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date

class StudentAttendanceBase(BaseModel):
    subject_name: str
    total_classes: int
    attended_classes: int
    percentage: float
    semester: int

class StudentAttendanceResponse(StudentAttendanceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class StudentSubjectMarksBase(BaseModel):
    subject_name: str
    marks_obtained: float
    total_marks: float
    grade: Optional[str] = None
    semester: int

class StudentSubjectMarksResponse(StudentSubjectMarksBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class StudentFeeRecordBase(BaseModel):
    total_fee: float
    paid_fee: float
    pending_fee: float
    due_date: Optional[date] = None
    semester: int

class StudentFeeRecordResponse(StudentFeeRecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class StudentDashboardResponse(BaseModel):
    current_semester: int
    overall_attendance: float
    pending_fees: float
    latest_percentage: float
    recent_notices_count: int

