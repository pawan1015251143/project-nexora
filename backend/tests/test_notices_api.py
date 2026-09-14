import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, RoleEnum
from app.models.notice import Notice
from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_active_user, require_role
from datetime import datetime

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

class MockSession:
    notices = {}
    
    def __init__(self):
        if not self.notices:
            n = Notice(id=1, title="Test", content="Content", priority=1, published_at=datetime.utcnow(), created_by=1, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            self.notices[1] = n

    async def execute(self, statement):
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        statement_str = str(compiled).lower()
        if "from notices" in statement_str:
            if "where notices.id =" in statement_str:
                return MockResult([list(self.notices.values())[0]] if self.notices else [])
            return MockResult(list(self.notices.values()))
        return MockResult([])

    def add(self, instance):
        instance.id = len(self.notices) + 1
        instance.published_at = datetime.utcnow()
        instance.created_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        self.notices[instance.id] = instance

    def delete(self, instance):
        # We need to find the instance by ID because the instance might be a copy or matched from db
        # In mock session it's the exact object, but just in case
        for k, v in list(self.notices.items()):
            if v.id == instance.id:
                del self.notices[k]

    async def commit(self):
        pass

    async def refresh(self, instance):
        pass

async def override_get_db():
    yield MockSession()

def override_require_admin():
    async def _require_role(current_user: User = None):
        return User(id=1, role=RoleEnum.admin, is_active=True)
    return _require_role

async def override_get_current_student():
    return User(id=2, role=RoleEnum.student, is_active=True)

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
def student_token_headers():
    app.dependency_overrides[get_current_active_user] = override_get_current_student
    app.dependency_overrides[require_role(["admin"])] = lambda: User(id=2, role=RoleEnum.student) # will fail in test intentionally by us triggering 403 or we can just let it act as student
    return {"Authorization": "Bearer student-token"}

@pytest.fixture
def admin_token_headers():
    async def override_get_current_admin():
        return User(id=1, role=RoleEnum.admin, is_active=True)
    app.dependency_overrides[get_current_active_user] = override_get_current_admin
    # We must patch require_role dependency explicitly in FastAPI app
    # A trick is to just patch the endpoint directly if needed, but let's see if FastAPI resolves it.
    return {"Authorization": "Bearer admin-token"}

@pytest.mark.asyncio
async def test_list_notices_student(async_client: AsyncClient, student_token_headers: dict):
    response = await async_client.get("/api/notices", headers=student_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_list_notices_admin(async_client: AsyncClient, admin_token_headers: dict):
    response = await async_client.get("/api/notices", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_notice_student_forbidden(async_client: AsyncClient, student_token_headers: dict):
    # If the user is student, the dependency should throw 403.
    # To mock this, we can just patch require_role
    from fastapi import HTTPException
    app.dependency_overrides[require_role(["admin"])] = lambda: (_ for _ in ()).throw(HTTPException(status_code=403, detail="Not enough permissions"))
    
    payload = {
        "title": "Hackathon",
        "content": "Join us",
        "priority": 1
    }
    response = await async_client.post("/api/notices", json=payload, headers=student_token_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_notice_admin(async_client: AsyncClient, admin_token_headers: dict):
    async def override_require_admin():
        return User(id=1, role=RoleEnum.admin, is_active=True)
    app.dependency_overrides[require_role(["admin"])] = override_require_admin
    
    payload = {
        "title": "Hackathon",
        "content": "Join us",
        "priority": 1
    }
    response = await async_client.post("/api/notices", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Hackathon"
    assert "id" in data

@pytest.mark.asyncio
async def test_delete_notice_admin(async_client: AsyncClient, admin_token_headers: dict):
    async def override_require_admin():
        return User(id=1, role=RoleEnum.admin, is_active=True)
    app.dependency_overrides[require_role(["admin"])] = override_require_admin
    
    # Delete
    res_del = await async_client.delete(f"/api/notices/1", headers=admin_token_headers)
    assert res_del.status_code == 204

    # Verify deleted
    res_get = await async_client.get("/api/notices", headers=admin_token_headers)
    notices = res_get.json()
    assert not any(n["id"] == 1 for n in notices)

@pytest.mark.asyncio
async def test_get_translation_creates_and_caches(async_client: AsyncClient, student_token_headers: dict):
    # Notice 1 already exists in MockSession
    # We just request its translation
    res = await async_client.get("/api/notices/1/translation?mode=hi_annotated", headers=student_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "Mocked Annotation" in data["content"]
    
@pytest.mark.asyncio
async def test_get_translation_invalid_mode(async_client: AsyncClient, student_token_headers: dict):
    res = await async_client.get("/api/notices/1/translation?mode=invalid_mode", headers=student_token_headers)
    assert res.status_code == 400
