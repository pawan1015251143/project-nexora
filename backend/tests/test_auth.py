import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.db.database import get_db
from app.models.user import User, RoleEnum
from app.security.auth import get_password_hash, create_access_token
from datetime import datetime, timedelta

# Mock Database Session
class MockResult:
    def __init__(self, user):
        self._user = user
    def scalars(self):
        class MockScalars:
            def first(self):
                return self._user
        mock_scalars = MockScalars()
        mock_scalars._user = self._user
        return mock_scalars

class MockSession:
    def __init__(self):
        self.users = {} # Mock DB state: email -> User
        
        # Seed an admin user
        admin_user = User(
            id=1,
            name="Admin User",
            email="admin@college.edu",
            password_hash=get_password_hash("adminpass"),
            role=RoleEnum.admin,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users[admin_user.email] = admin_user
        
        # Seed a student user
        student_user = User(
            id=2,
            name="Student User",
            email="student@college.edu",
            password_hash=get_password_hash("studentpass"),
            role=RoleEnum.student,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users[student_user.email] = student_user

    async def execute(self, statement):
        # Parse the statement with literal binds to see the actual values
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        statement_str = str(compiled)
        for email, user in self.users.items():
            if email in statement_str:
                return MockResult(user)
        return MockResult(None)

    def add(self, instance):
        if isinstance(instance, User):
            instance.id = len(self.users) + 1
            if not instance.created_at:
                instance.created_at = datetime.utcnow()
            if not instance.updated_at:
                instance.updated_at = datetime.utcnow()
            if instance.is_active is None:
                instance.is_active = True
            self.users[instance.email] = instance

    async def commit(self):
        pass

    async def refresh(self, instance):
        pass

async def override_get_db():
    yield MockSession()

@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_valid_registration(async_client):
    response = await async_client.post("/api/auth/register", json={
        "name": "New User",
        "email": "new@college.edu",
        "password": "newpassword",
        "role": "student"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@college.edu"
    assert "password" not in data

@pytest.mark.asyncio
async def test_duplicate_registration(async_client):
    response = await async_client.post("/api/auth/register", json={
        "name": "Student User",
        "email": "student@college.edu", # Already seeded
        "password": "password"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_valid_login(async_client):
    response = await async_client.post("/api/auth/login", data={
        "username": "student@college.edu",
        "password": "studentpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_invalid_password(async_client):
    response = await async_client.post("/api/auth/login", data={
        "username": "student@college.edu",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_protected_endpoint(async_client):
    # Get token first
    login_res = await async_client.post("/api/auth/login", data={
        "username": "student@college.edu",
        "password": "studentpass"
    })
    token = login_res.json()["access_token"]
    
    # Access protected route
    response = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "student@college.edu"

@pytest.mark.asyncio
async def test_invalid_token(async_client):
    response = await async_client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.asyncio
async def test_role_restriction_student_denied(async_client):
    # Login as student
    login_res = await async_client.post("/api/auth/login", data={
        "username": "student@college.edu",
        "password": "studentpass"
    })
    token = login_res.json()["access_token"]
    
    # Attempt to access admin route
    response = await async_client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"

@pytest.mark.asyncio
async def test_role_restriction_admin_allowed(async_client):
    # Login as admin
    login_res = await async_client.post("/api/auth/login", data={
        "username": "admin@college.edu",
        "password": "adminpass"
    })
    token = login_res.json()["access_token"]
    
    # Attempt to access admin route
    response = await async_client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "Welcome admin" in response.json()["message"]
