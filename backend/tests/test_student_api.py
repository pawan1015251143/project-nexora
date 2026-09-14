import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, date

from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, RoleEnum
from app.models.student_data import StudentAttendance, StudentSubjectMarks, StudentFeeRecord
from app.models.notice import Notice

class MockResult:
    def __init__(self, data):
        self._data = data
    def scalars(self):
        class MockScalars:
            def __init__(self, data):
                self._data = data
            def first(self):
                return self._data[0] if self._data else None
            def all(self):
                return self._data
        return MockScalars(self._data)
    def scalar_one_or_none(self):
        return self._data[0] if self._data else None

class MockStudentSession:
    def __init__(self):
        self.attendances = [
            StudentAttendance(id=1, user_id=2, subject_name="DBMS", total_classes=40, attended_classes=33, percentage=82.5, semester=3)
        ]
        self.marks = [
            StudentSubjectMarks(id=1, user_id=2, subject_name="DBMS", marks_obtained=85, total_marks=100, grade="A", semester=2)
        ]
        self.fees = [
            StudentFeeRecord(id=1, user_id=2, total_fee=50000.0, paid_fee=35000.0, pending_fee=15000.0, due_date=date(2026, 10, 15), semester=3)
        ]
        self.notices = [
            Notice(id=1, title="Test", content="Content", published_at=datetime.utcnow())
        ]

    async def execute(self, statement):
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        statement_str = str(compiled).lower()
        
        if "from student_attendance" in statement_str:
            return MockResult(self.attendances)
        elif "from student_subject_marks" in statement_str:
            return MockResult(self.marks)
        elif "from student_fee_records" in statement_str:
            return MockResult(self.fees)
        elif "from notices" in statement_str:
            return MockResult(self.notices)
        return MockResult([])

async def override_get_db():
    yield MockStudentSession()

async def override_get_current_student():
    return User(id=2, role=RoleEnum.student, is_active=True, semester=3)

@pytest.fixture
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_student
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
async def async_client(override_dependencies):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_get_dashboard(async_client: AsyncClient):
    res = await async_client.get("/api/student/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["current_semester"] == 3
    assert data["overall_attendance"] == 82.5
    assert data["pending_fees"] == 15000.0
    assert data["latest_percentage"] == 85.0
    assert data["recent_notices_count"] == 1

@pytest.mark.asyncio
async def test_get_attendance(async_client: AsyncClient):
    res = await async_client.get("/api/student/attendance")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["subject_name"] == "DBMS"

@pytest.mark.asyncio
async def test_get_marks(async_client: AsyncClient):
    res = await async_client.get("/api/student/marks")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["grade"] == "A"

@pytest.mark.asyncio
async def test_get_fees(async_client: AsyncClient):
    res = await async_client.get("/api/student/fees")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["pending_fee"] == 15000.0
