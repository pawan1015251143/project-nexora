import pytest
from httpx import AsyncClient, ASGITransport
import io
from app.main import app
from app.db.database import get_db
from app.models.user import User, RoleEnum
from app.models.document import Document, DocumentStatusEnum
from app.security.auth import get_password_hash
from datetime import datetime
from app.utils.file_utils import UPLOAD_DIR
import os
import shutil

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

class MockSession:
    # Use class-level dictionaries to persist state across API calls
    users = {}
    documents = {}
    
    def __init__(self):
        # Seed an admin user
        admin_user = User(
            id=1,
            name="Admin User",
            email="admin@college.edu",
            password_hash=get_password_hash("adminpass"),
            role=RoleEnum.admin,
            is_active=True
        )
        self.users[admin_user.email] = admin_user
        
        # Seed a student user
        student_user = User(
            id=2,
            name="Student User",
            email="student@college.edu",
            password_hash=get_password_hash("studentpass"),
            role=RoleEnum.student,
            is_active=True
        )
        self.users[student_user.email] = student_user

    async def execute(self, statement):
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        statement_str = str(compiled).lower()
        
        if "from users" in statement_str:
            for email, user in self.users.items():
                if email in statement_str:
                    return MockResult([user])
            return MockResult([])
            
        if "from documents" in statement_str:
            # Check for id match (e.g. "where documents.id = 1")
            for doc_id, doc in self.documents.items():
                if f"documents.id = {doc_id}" in statement_str:
                    return MockResult([doc])
            
            # Match all (for list_documents)
            docs = list(self.documents.values())
            return MockResult(docs)
            
        return MockResult([])

    def add(self, instance):
        if isinstance(instance, Document):
            instance.id = len(self.documents) + 1
            if not instance.created_at:
                instance.created_at = datetime.utcnow()
            if not instance.updated_at:
                instance.updated_at = datetime.utcnow()
            if not getattr(instance, "version", None):
                instance.version = 1
            self.documents[instance.id] = instance

    async def commit(self):
        pass

    async def refresh(self, instance):
        pass

    async def rollback(self):
        pass

    async def delete(self, instance):
        if isinstance(instance, Document) and instance.id in self.documents:
            del self.documents[instance.id]

async def override_get_db():
    yield MockSession()

@pytest.fixture
def override_db_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def async_client(override_db_dependency):
    # Ensure upload dir is empty before tests
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)

@pytest.fixture
async def admin_token(async_client):
    res = await async_client.post("/api/auth/login", data={"username": "admin@college.edu", "password": "adminpass"})
    return res.json()["access_token"]

@pytest.fixture
async def student_token(async_client):
    res = await async_client.post("/api/auth/login", data={"username": "student@college.edu", "password": "studentpass"})
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_upload_document_admin(async_client, admin_token):
    file_content = b"This is a test PDF content."
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"title": "Test Syllabus", "category": "Syllabus"}
    
    response = await async_client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        data=data,
        files=files
    )
    
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["title"] == "Test Syllabus"
    assert res_data["mime_type"] == "application/pdf"
    assert res_data["status"] == "uploaded"
    assert "file_path" in res_data
    
    # Verify file physically exists
    assert os.path.exists(res_data["file_path"])

@pytest.mark.asyncio
async def test_upload_document_student_forbidden(async_client, student_token):
    file_content = b"This is a test PDF content."
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"title": "Test Syllabus"}
    
    response = await async_client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {student_token}"},
        data=data,
        files=files
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_invalid_file_type(async_client, admin_token):
    file_content = b"print('hello')"
    files = {"file": ("test.py", io.BytesIO(file_content), "text/x-python")}
    data = {"title": "Bad File"}
    
    response = await async_client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        data=data,
        files=files
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_document_deletion(async_client, admin_token):
    # Upload first
    file_content = b"Content to delete"
    files = {"file": ("delete_me.txt", io.BytesIO(file_content), "text/plain")}
    data = {"title": "Delete Target"}
    
    upload_res = await async_client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        data=data,
        files=files
    )
    doc_id = upload_res.json()["id"]
    file_path = upload_res.json()["file_path"]
    
    assert os.path.exists(file_path)
    
    # Delete it
    del_res = await async_client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert del_res.status_code == 204
    assert not os.path.exists(file_path) # Physical file should be gone
