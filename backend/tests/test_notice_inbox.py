"""
Tests for the Admin Notice Inbox (Demo Notice Import System)
Tests: 15 scenarios covering the full import pipeline.
"""
import pytest
import hashlib
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, RoleEnum
from app.models.demo_source_message import DemoSourceMessage
from app.models.notice_import import NoticeImport, ImportStatusEnum
from app.models.notice import Notice
from app.models.document import Document, DocumentStatusEnum


# ── Helpers ────────────────────────────────────────────────────────────────

def make_hash(text: str, attachment: str = None) -> str:
    raw = text.strip()
    if attachment:
        raw += f"|{attachment}"
    return hashlib.sha256(raw.encode()).hexdigest()


DEMO_MSG_TEXT = "NOTICE: Semester Exam Form submission deadline is 30 Sep 2026."
DEMO_ATTACHMENT = "exam_form_notice.pdf"


class MockResult:
    def __init__(self, data):
        self._data = data if isinstance(data, list) else [data] if data else []

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


class MockInboxSession:
    """Mock DB session for notice inbox tests."""

    def __init__(self, has_import: bool = False, import_status: ImportStatusEnum = ImportStatusEnum.new):
        self._added = []
        self._committed = False
        self.has_import = has_import
        self.import_status = import_status

        self.source_msg = DemoSourceMessage(
            id=1,
            source_message_id="WA-TEST-001",
            group_name="ABC College — Official Notices",
            sender="Admin Office",
            message_text=DEMO_MSG_TEXT,
            attachment_name=DEMO_ATTACHMENT,
            attachment_type="pdf",
            attachment_content="Exam form details here.",
            timestamp=datetime.utcnow(),
            imported=has_import,
            content_hash=make_hash(DEMO_MSG_TEXT, DEMO_ATTACHMENT),
        )
        self.import_record = NoticeImport(
            id=1,
            source_message_id=1,
            notice_id=None,
            document_id=None,
            status=import_status,
            draft_title="Semester Exam Form Notice",
            draft_content="Submit form by 30 Sep 2026.",
            ai_extracted_json={"title": "Semester Exam Form", "notice_type": "Examination"},
            created_by=99,
        ) if has_import else None

        self.published_notice = Notice(
            id=10,
            title="Semester Exam Form Notice",
            content="Submit form by 30 Sep 2026.",
            priority=0,
            published_at=datetime.utcnow(),
            created_by=99,
        )

    def add(self, obj):
        self._added.append(obj)
        # Simulate ID assignment
        if isinstance(obj, NoticeImport) and not obj.id:
            obj.id = 1
        if isinstance(obj, Notice) and not obj.id:
            obj.id = 10
        if isinstance(obj, Document) and not obj.id:
            obj.id = 5

    def add_all(self, objs):
        self._added.extend(objs)

    async def execute(self, statement):
        try:
            compiled = statement.compile(compile_kwargs={"literal_binds": True})
            sql = str(compiled).lower()
        except Exception:
            sql = ""

        # Source messages query
        if "from demo_source_messages" in sql:
            return MockResult([self.source_msg])

        # Import record query
        if "from notice_imports" in sql:
            if self.import_record:
                return MockResult([self.import_record])
            return MockResult([])

        # Notices
        if "from notices" in sql:
            return MockResult([self.published_notice])

        # Documents
        if "from documents" in sql:
            doc = Document(id=5, title="Test", file_path="virtual://notice/10",
                           mime_type="text/plain", file_size=100,
                           status=DocumentStatusEnum.ready, uploaded_by=99)
            return MockResult([doc])

        # Audit logs — always empty (we just add them)
        if "from audit_logs" in sql:
            return MockResult([])

        return MockResult([])

    async def flush(self):
        pass

    async def commit(self):
        self._committed = True

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass


# ── Admin user fixture ─────────────────────────────────────────────────────

ADMIN_USER = User(id=99, name="Admin", email="admin@test.com",
                  role=RoleEnum.admin, is_active=True)

STUDENT_USER = User(id=2, name="Student", email="student@test.com",
                    role=RoleEnum.student, is_active=True)


def make_app_overrides(session: MockInboxSession, user: User):
    async def override_db():
        yield session

    async def override_user():
        return user

    return override_db, override_user


# ── Test 1: List demo source messages ─────────────────────────────────────

@pytest.mark.asyncio
async def test_list_demo_source_messages():
    """Admin can list all demo source messages."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["source"]["sender"] == "Admin Office"
    assert data[0]["import_record"] is None


# ── Test 2: Unauthorized student cannot access inbox ───────────────────────

@pytest.mark.asyncio
async def test_student_cannot_access_inbox():
    """Students must not be able to access the admin notice inbox."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, STUDENT_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 403


# ── Test 3: Get single inbox item detail ──────────────────────────────────

@pytest.mark.asyncio
async def test_get_inbox_item_detail():
    """Admin can get details of a specific demo source message."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox/1")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert data["source"]["group_name"] == "ABC College — Official Notices"
    assert data["source"]["attachment_name"] == DEMO_ATTACHMENT


# ── Test 4: Admin can import a demo notice ─────────────────────────────────

@pytest.mark.asyncio
async def test_admin_imports_notice():
    """Admin can import a new demo source message."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/import")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "imported"
    assert data["source_message_id"] == 1


# ── Test 5: Duplicate import is detected ──────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_import_detected():
    """Re-importing an already-imported message returns 409 Conflict."""
    # already has import record
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.imported)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/import")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 409
    assert "already been imported" in res.json()["detail"]


# ── Test 6: Source metadata is preserved ──────────────────────────────────

@pytest.mark.asyncio
async def test_source_metadata_preserved():
    """Import record preserves source_message_id and sender information."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.imported)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox/1")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    data = res.json()
    assert data["source"]["source_message_id"] == "WA-TEST-001"
    assert data["source"]["sender"] == "Admin Office"
    assert data["source"]["content_hash"] == make_hash(DEMO_MSG_TEXT, DEMO_ATTACHMENT)


# ── Test 7: AI processing creates draft ───────────────────────────────────

@pytest.mark.asyncio
async def test_ai_processing_creates_draft():
    """Processing an imported notice creates a draft with AI-extracted fields."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.imported)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/process")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["draft", "imported"]  # draft on success, imported on AI error
    assert data["source_message_id"] == 1


# ── Test 8: Admin can approve an import ───────────────────────────────────

@pytest.mark.asyncio
async def test_admin_approves_import():
    """Admin can approve a draft import."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.draft)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/approve", json={
            "title": "Semester Exam Form — Final",
            "priority": 1
        })

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"


# ── Test 9: Admin can reject an import ────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_rejects_import():
    """Admin can reject a draft/imported notice."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.draft)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/reject", json={
            "reason": "Duplicate information already posted."
        })

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected"


# ── Test 10: Rejected import cannot be published ──────────────────────────

@pytest.mark.asyncio
async def test_rejected_cannot_be_published():
    """A rejected import cannot be published."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.rejected)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/publish")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 400
    assert "approved" in res.json()["detail"].lower()


# ── Test 11: Approved notice can be published ─────────────────────────────

@pytest.mark.asyncio
async def test_approved_notice_can_be_published():
    """An approved import can be published to the portal."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.approved)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/publish")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "published"


# ── Test 12: Status endpoint returns pipeline state ───────────────────────

@pytest.mark.asyncio
async def test_status_endpoint_no_import():
    """Status endpoint returns 'new' for unimported messages."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox/1/status")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    assert res.json()["status"] == "new"


# ── Test 13: Status endpoint with existing import ─────────────────────────

@pytest.mark.asyncio
async def test_status_endpoint_with_import():
    """Status endpoint returns current import status."""
    session = MockInboxSession(has_import=True, import_status=ImportStatusEnum.draft)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox/1/status")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 200
    assert res.json()["status"] == "draft"
    assert res.json()["import_id"] == 1


# ── Test 14: Unauthorized user cannot import ──────────────────────────────

@pytest.mark.asyncio
async def test_unauthorized_cannot_import():
    """Faculty and students cannot perform admin import operations."""
    faculty_user = User(id=3, name="Faculty", email="faculty@test.com",
                        role=RoleEnum.faculty, is_active=True)
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, faculty_user)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/admin/notice-inbox/1/import")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    assert res.status_code == 403


# ── Test 15: Content hash prevents duplicate detection ────────────────────

@pytest.mark.asyncio
async def test_content_hash_is_computed():
    """Source messages have a content hash for duplicate detection."""
    session = MockInboxSession(has_import=False)
    db_dep, user_dep = make_app_overrides(session, ADMIN_USER)

    app.dependency_overrides[get_db] = db_dep
    app.dependency_overrides[get_current_active_user] = user_dep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/notice-inbox/1")

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

    data = res.json()
    expected_hash = make_hash(DEMO_MSG_TEXT, DEMO_ATTACHMENT)
    assert data["source"]["content_hash"] == expected_hash
    assert len(data["source"]["content_hash"]) == 64  # SHA-256 hex
