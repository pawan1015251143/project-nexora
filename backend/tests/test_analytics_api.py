import pytest
from httpx import AsyncClient, ASGITransport
from app.models.user import User, RoleEnum
from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_active_user, require_role

class MockResult:
    def __init__(self, val):
        self.val = val
    def scalar(self):
        return self.val
    def all(self):
        return self.val

class MockSession:
    async def execute(self, statement):
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        stmt_str = str(compiled).lower()
        
        if "group by" in stmt_str:
            # mock chart responses
            class RowMock:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
                        
            from datetime import datetime
            return MockResult([RowMock(date=datetime.utcnow(), count=5, category="Test", title="Doc", name="Dept", rating=True)])
            
        if "count(users.id)" in stmt_str:
            return MockResult(10)
        if "count(documents.id)" in stmt_str:
            return MockResult(5)
        if "count(messages.id)" in stmt_str:
            return MockResult(20)
        if "count(feedback.id)" in stmt_str:
            return MockResult(2)
            
        return MockResult(0)

async def override_get_db():
    yield MockSession()

@pytest.fixture
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def async_client(override_dependencies):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def admin_token_headers():
    async def override_get_current_admin():
        return User(id=1, role=RoleEnum.admin, is_active=True)
    app.dependency_overrides[get_current_active_user] = override_get_current_admin
    return {"Authorization": "Bearer admin-token"}

@pytest.fixture
def student_token_headers():
    async def override_get_current_student():
        return User(id=2, role=RoleEnum.student, is_active=True)
    app.dependency_overrides[get_current_active_user] = override_get_current_student
    return {"Authorization": "Bearer student-token"}

@pytest.mark.asyncio
async def test_get_metrics_admin(async_client: AsyncClient, admin_token_headers: dict):
    res = await async_client.get("/api/analytics/metrics", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert data["total_students"] == 10

@pytest.mark.asyncio
async def test_get_charts_admin(async_client: AsyncClient, admin_token_headers: dict):
    res = await async_client.get("/api/analytics/charts", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "questions_over_time" in data

@pytest.mark.asyncio
async def test_get_metrics_student_forbidden(async_client: AsyncClient, student_token_headers: dict):
    res = await async_client.get("/api/analytics/metrics", headers=student_token_headers)
    assert res.status_code == 403
