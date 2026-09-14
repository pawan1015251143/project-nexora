import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, date

from app.db.database import async_session_maker
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.student_data import StudentAttendance, StudentSubjectMarks, StudentFeeRecord
from app.security.auth import get_password_hash

async def seed_demo_student():
    async with async_session_maker() as session:
        # Create department if not exists
        stmt = select(Department).where(Department.name == "BCA")
        result = await session.execute(stmt)
        bca_dept = result.scalars().first()

        if not bca_dept:
            bca_dept = Department(name="BCA", description="Bachelor of Computer Applications")
            session.add(bca_dept)
            await session.commit()
            await session.refresh(bca_dept)

        # Check if Rahul exists
        stmt = select(User).where(User.email == "rahul@college.edu")
        result = await session.execute(stmt)
        rahul = result.scalars().first()

        if not rahul:
            print("Creating demo student Rahul Kumar...")
            rahul = User(
                name="Rahul Kumar",
                email="rahul@college.edu",
                password_hash=get_password_hash("password123"),
                role=RoleEnum.student,
                department_id=bca_dept.id,
                semester=3,
                is_active=True
            )
            session.add(rahul)
            await session.commit()
            await session.refresh(rahul)
        else:
            print("Demo student already exists. Cleaning up old data...")
            # Cleanup old data to re-seed fresh
            await session.execute(StudentAttendance.__table__.delete().where(StudentAttendance.user_id == rahul.id))
            await session.execute(StudentSubjectMarks.__table__.delete().where(StudentSubjectMarks.user_id == rahul.id))
            await session.execute(StudentFeeRecord.__table__.delete().where(StudentFeeRecord.user_id == rahul.id))
            await session.commit()

        print("Seeding Attendance...")
        attendances = [
            StudentAttendance(user_id=rahul.id, subject_name="DBMS", total_classes=40, attended_classes=33, percentage=82.5, semester=3),
            StudentAttendance(user_id=rahul.id, subject_name="Java", total_classes=42, attended_classes=32, percentage=76.2, semester=3),
            StudentAttendance(user_id=rahul.id, subject_name="Python", total_classes=35, attended_classes=32, percentage=91.4, semester=3),
            StudentAttendance(user_id=rahul.id, subject_name="Web Development", total_classes=40, attended_classes=34, percentage=85.0, semester=3),
        ]
        session.add_all(attendances)

        print("Seeding Marks...")
        marks = [
            StudentSubjectMarks(user_id=rahul.id, subject_name="DBMS", marks_obtained=85, total_marks=100, grade="A", semester=2),
            StudentSubjectMarks(user_id=rahul.id, subject_name="Java", marks_obtained=78, total_marks=100, grade="B+", semester=2),
            StudentSubjectMarks(user_id=rahul.id, subject_name="Data Structures", marks_obtained=92, total_marks=100, grade="O", semester=2),
            StudentSubjectMarks(user_id=rahul.id, subject_name="Mathematics", marks_obtained=74, total_marks=100, grade="B", semester=2),
        ]
        session.add_all(marks)

        print("Seeding Fees...")
        fees = [
            StudentFeeRecord(user_id=rahul.id, total_fee=50000.0, paid_fee=35000.0, pending_fee=15000.0, due_date=date(2026, 10, 15), semester=3),
            StudentFeeRecord(user_id=rahul.id, total_fee=50000.0, paid_fee=50000.0, pending_fee=0.0, due_date=date(2026, 4, 15), semester=2)
        ]
        session.add_all(fees)

        await session.commit()
        print("Demo data seeded successfully! Student: rahul@college.edu / password123")

if __name__ == "__main__":
    asyncio.run(seed_demo_student())
