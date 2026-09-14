from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.database import get_db
from app.models.user import User, RoleEnum
from app.models.student_data import StudentAttendance, StudentSubjectMarks, StudentFeeRecord
from app.models.notice import Notice
from app.api.deps import get_current_active_user
from app.schemas.student import (
    StudentAttendanceResponse,
    StudentSubjectMarksResponse,
    StudentFeeRecordResponse,
    StudentDashboardResponse
)

router = APIRouter()

@router.get("/dashboard", response_model=StudentDashboardResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    # Get Attendance
    stmt = select(StudentAttendance).where(StudentAttendance.user_id == current_user.id)
    result = await db.execute(stmt)
    attendances = result.scalars().all()
    overall_attendance = 0.0
    if attendances:
        overall_attendance = sum([a.percentage for a in attendances]) / len(attendances)

    # Get Fees
    stmt = select(StudentFeeRecord).where(StudentFeeRecord.user_id == current_user.id)
    result = await db.execute(stmt)
    fees = result.scalars().all()
    pending_fees = sum([f.pending_fee for f in fees])

    # Get Marks (Latest percentage approximation)
    stmt = select(StudentSubjectMarks).where(StudentSubjectMarks.user_id == current_user.id)
    result = await db.execute(stmt)
    marks = result.scalars().all()
    latest_percentage = 0.0
    if marks:
        total_obtained = sum([m.marks_obtained for m in marks])
        total_max = sum([m.total_marks for m in marks])
        if total_max > 0:
            latest_percentage = (total_obtained / total_max) * 100

    # Get Recent Notices count (just all published)
    stmt = select(Notice).where(Notice.published_at != None)
    result = await db.execute(stmt)
    notices = result.scalars().all()
    recent_notices_count = len(notices)

    return StudentDashboardResponse(
        current_semester=current_user.semester or 1,
        overall_attendance=overall_attendance,
        pending_fees=pending_fees,
        latest_percentage=latest_percentage,
        recent_notices_count=recent_notices_count
    )

@router.get("/attendance", response_model=List[StudentAttendanceResponse])
async def get_attendance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(StudentAttendance).where(StudentAttendance.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/marks", response_model=List[StudentSubjectMarksResponse])
async def get_marks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(StudentSubjectMarks).where(StudentSubjectMarks.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/fees", response_model=List[StudentFeeRecordResponse])
async def get_fees(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(StudentFeeRecord).where(StudentFeeRecord.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()
