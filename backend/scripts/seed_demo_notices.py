"""
Seed Demo Notice Source Messages
Populates the ABC College WhatsApp demo group with 5 realistic notice messages.
Run: python scripts/seed_demo_notices.py
"""
import asyncio
import hashlib
import sys
import os
from datetime import datetime, timedelta

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.models.demo_source_message import DemoSourceMessage
from app.db.database import DATABASE_URL, normalize_database_url

DB_URL = normalize_database_url(os.getenv("DATABASE_URL", DATABASE_URL))


def compute_hash(message_text: str, attachment_name: str = None) -> str:
    raw = message_text.strip()
    if attachment_name:
        raw += f"|{attachment_name}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


DEMO_MESSAGES = [
    {
        "source_message_id": "WA-ABC-2026-001",
        "group_name": "ABC College — Official Notices",
        "sender": "Admin Office",
        "message_text": """NOTICE: Semester Examination Form Submission

All students are hereby informed that the Semester Examination Form (Odd Semester 2026-27) must be submitted on or before 30 September 2026.

Important Instructions:
1. Log in to the college student portal to fill the examination form.
2. Pay the examination fee of ₹500/- through the online payment gateway.
3. Download and retain the filled form for future reference.
4. Students with pending library dues will NOT be allowed to appear in examinations.
5. Contact the Examination Cell (Ext: 201) for any queries.

Last Date: 30 September 2026
Examination Controller
ABC College of Engineering, Pune""",
        "attachment_name": "semester_exam_form_notice_2026.pdf",
        "attachment_type": "pdf",
        "attachment_content": """SEMESTER EXAMINATION FORM SUBMISSION NOTICE
Academic Year: 2026-27 | Odd Semester

Eligible Students: B.Tech (1st to 4th Year), M.Tech (1st to 2nd Year)

Examination Fee Structure:
- Regular Students: ₹500/-
- ATKT Students: ₹750/-

Payment Modes: Online Portal / Bank Challan

Verification:
After form submission, students must get the form verified by the Head of Department between 1 Oct - 5 Oct 2026.

Office Hours: Monday to Saturday, 10:00 AM to 4:00 PM
Examination Cell, Block B, Room No. 204
ABC College of Engineering, Pune - 411041
Email: exam@abccollege.edu.in | Phone: 020-27654321""",
        "timestamp": datetime.utcnow() - timedelta(days=5),
    },
    {
        "source_message_id": "WA-ABC-2026-002",
        "group_name": "ABC College — Official Notices",
        "sender": "Examination Cell",
        "message_text": """End Semester Examination Schedule 2026-27 (Odd Semester) has been released.

Students are advised to check the examination schedule carefully.

Key Points:
• Examinations commence from 15 November 2026
• Hall Ticket/Admit Card can be downloaded from student portal after 5 November 2026
• Bring your Admit Card and College ID for every examination
• Examination Venue: Main Building & Annex Block

No student will be permitted to appear without a valid Admit Card.

For any discrepancy in the schedule, contact: examcell@abccollege.edu.in

Examination Controller
ABC College""",
        "attachment_name": "end_semester_exam_schedule_2026.pdf",
        "attachment_type": "pdf",
        "attachment_content": """END SEMESTER EXAMINATION SCHEDULE 2026-27 (ODD SEMESTER)
B.Tech — Computer Engineering (3rd Year)

Date | Subject | Code | Time | Venue
15 Nov 2026 | Data Structures & Algorithms | CSE301 | 10:00 AM - 1:00 PM | Hall A
18 Nov 2026 | Operating Systems | CSE303 | 10:00 AM - 1:00 PM | Hall B
21 Nov 2026 | Computer Networks | CSE305 | 10:00 AM - 1:00 PM | Hall A
24 Nov 2026 | Database Management Systems | CSE307 | 10:00 AM - 1:00 PM | Hall C
27 Nov 2026 | Theory of Computation | CSE309 | 10:00 AM - 1:00 PM | Hall A

Important:
- Reporting Time: 9:30 AM
- No electronic gadgets permitted in examination hall
- Use of unfair means will lead to cancellation of examination""",
        "timestamp": datetime.utcnow() - timedelta(days=3),
    },
    {
        "source_message_id": "WA-ABC-2026-003",
        "group_name": "ABC College — Official Notices",
        "sender": "Academic Section",
        "message_text": """NOTICE: Internal Assessment (IA) Schedule — Unit Test III

All students of B.Tech (All Branches) are informed that Unit Test III (Internal Assessment) will be conducted as per the schedule below.

Unit Test III covers syllabus from Unit 4 & Unit 5.

Students must carry their college ID card to appear for the internal assessment.
Minimum 40% marks required in internal assessment to be eligible for end-semester examination.

Contact your respective Class Coordinator for subject-wise IA schedule.

Signed,
Academic Dean
ABC College of Engineering""",
        "attachment_name": "internal_assessment_schedule_oct2026.pdf",
        "attachment_type": "pdf",
        "attachment_content": """INTERNAL ASSESSMENT III SCHEDULE
B.Tech — All Branches | October 2026

Date | Branch | Subjects
10 Oct 2026 | Computer Engineering | DSA, OS, Computer Networks
11 Oct 2026 | Mechanical Engineering | Thermodynamics, Fluid Mechanics
12 Oct 2026 | Electronics Engineering | Digital Electronics, VLSI Design
13 Oct 2026 | Civil Engineering | Structural Analysis, Geotechnical Engineering

Time: 11:00 AM - 12:30 PM (for all)
Venue: Respective Department Classrooms

Students who miss Unit Test III due to medical reasons must submit a medical certificate within 3 days.
Make-up test: 20 Oct 2026 (subject to approval by HOD)""",
        "timestamp": datetime.utcnow() - timedelta(days=7),
    },
    {
        "source_message_id": "WA-ABC-2026-004",
        "group_name": "ABC College — Official Notices",
        "sender": "Training & Placement Cell",
        "message_text": """Campus Placement 2026-27 Registration Open!

Dear Final Year Students,

The Training & Placement Cell is pleased to announce that campus placement registration for the academic year 2026-27 is now open.

Eligibility Criteria:
✅ B.Tech Final Year Students (2026-27 batch)
✅ Minimum CGPA: 6.0 (No active backlogs)
✅ All semesters marksheets must be submitted

Registration Deadline: 20 September 2026

Please visit the Placement Portal: placement.abccollege.edu.in to complete your registration.

Upload the following documents:
1. Updated Resume (PDF format)
2. Photograph (passport size)
3. All semester marksheets
4. Internship certificate (if any)

For assistance: placement@abccollege.edu.in | 020-27654329

Training & Placement Cell
ABC College of Engineering""",
        "attachment_name": "placement_registration_notice_2026.pdf",
        "attachment_type": "pdf",
        "attachment_content": """CAMPUS PLACEMENT 2026-27 — STUDENT REGISTRATION GUIDE

Companies Expected to Visit (Tentative):
- TCS | Date: Oct 2026 | Role: System Engineer | Package: 3.5-4.5 LPA
- Infosys | Date: Nov 2026 | Role: Software Engineer | Package: 4.0-5.0 LPA
- Wipro | Date: Nov 2026 | Role: Project Engineer | Package: 3.5 LPA
- Capgemini | Date: Dec 2026 | Role: Analyst | Package: 4.0-5.5 LPA
- L&T Technology Services | Date: Dec 2026 | Role: Engineer Trainee | Package: 4.5 LPA

Pre-Placement Activities:
- Aptitude Test Workshop: 1 Oct 2026, 2:00 PM, Seminar Hall
- Resume Building Session: 5 Oct 2026, 3:00 PM, Online (Teams)
- Mock Interview: 8 Oct 2026, by appointment

Important: Students must maintain regular attendance to remain eligible for placement activities.""",
        "timestamp": datetime.utcnow() - timedelta(days=10),
    },
    {
        "source_message_id": "WA-ABC-2026-005",
        "group_name": "ABC College — Official Notices",
        "sender": "Principal's Office",
        "message_text": """ACADEMIC CALENDAR — Holidays & Events (October-December 2026)

All students and faculty are hereby informed of the upcoming holidays, events, and important academic dates for the period October to December 2026.

Holidays:
• 2 October 2026 (Friday) — Gandhi Jayanti [National Holiday]
• 24 October 2026 (Saturday) — Dussehra [Regional Holiday]
• 1 November 2026 (Sunday) — Maharashtra Day
• 14 November 2026 (Saturday) — Diwali Vacation begins
• 19 November 2026 (Thursday) — Diwali Vacation ends
• 19 December 2026 (Friday) — Last day of instruction

College will remain OPEN on:
• 7 November 2026 (compensatory working day)

Academic Events:
• 15-16 October 2026 — Tech Fest "NEXUS 2026"
• 22 October 2026 — Industry Guest Lecture, CS Dept.
• 10 November 2026 — Sports Day
• 5 December 2026 — Annual Cultural Fest "UTSAV"

For complete calendar, visit: www.abccollege.edu.in/academic-calendar

Principal
ABC College of Engineering, Pune""",
        "attachment_name": "academic_calendar_oct_dec_2026.pdf",
        "attachment_type": "pdf",
        "attachment_content": """ABC COLLEGE OF ENGINEERING — ACADEMIC CALENDAR
Odd Semester 2026-27 | October - December 2026

COMPLETE HOLIDAY LIST:
1. Gandhi Jayanti: 2 October 2026 (National Holiday)
2. Dussehra: 24 October 2026
3. Diwali Vacation: 14 Nov - 18 Nov 2026 (5 days)
4. Christmas / Winter Break: 23-31 December 2026

KEY EXAMINATION DATES:
- End of Unit Test III: 13 October 2026
- Practical Examinations: 1-14 November 2026
- End Semester Theory Exams: 15 November - 10 December 2026
- Result Declaration: 31 December 2026

LAST DATE TO SUBMIT:
- Examination Form: 30 September 2026
- Placement Registration: 20 September 2026

Contact: principal@abccollege.edu.in
Website: www.abccollege.edu.in""",
        "timestamp": datetime.utcnow() - timedelta(days=1),
    },
]


async def seed():
    engine = create_async_engine(DB_URL, echo=False)

    @event.listens_for(engine.sync_engine, "do_connect")
    def _receive_do_connect(dialect, conn_rec, cargs, cparams):
        is_pgbouncer = cparams.pop("pgbouncer", None) is not None
        host = str(cparams.get("host", ""))
        port = cparams.get("port")
        if is_pgbouncer or "pooler.supabase.com" in host or port == 6543:
            cparams["statement_cache_size"] = 0

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        seeded = 0
        skipped = 0

        for data in DEMO_MESSAGES:
            # Check if already seeded
            result = await session.execute(
                select(DemoSourceMessage).where(
                    DemoSourceMessage.source_message_id == data["source_message_id"]
                )
            )
            existing = result.scalars().first()

            if existing:
                print(f"  [SKIP] {data['source_message_id']} already exists.")
                skipped += 1
                continue

            msg = DemoSourceMessage(
                source_message_id=data["source_message_id"],
                group_name=data["group_name"],
                sender=data["sender"],
                message_text=data["message_text"],
                attachment_name=data.get("attachment_name"),
                attachment_type=data.get("attachment_type"),
                attachment_content=data.get("attachment_content"),
                timestamp=data["timestamp"],
                imported=False,
                content_hash=compute_hash(
                    data["message_text"],
                    data.get("attachment_name")
                ),
            )
            session.add(msg)
            seeded += 1
            print(f"  [ADD]  {data['source_message_id']} — {data['sender']}: {data['message_text'][:60].strip()}...")

        await session.commit()
        print(f"\nDone. Seeded: {seeded}, Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    print("Seeding demo WhatsApp notice source messages...")
    asyncio.run(seed())
