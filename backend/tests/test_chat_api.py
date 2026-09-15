import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import get_db
from app.models.user import User, RoleEnum
from app.models.conversation import Conversation
from app.models.message import Message, MessageRoleEnum
from app.security.auth import get_password_hash
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
    users = {}
    conversations = {}
    messages = {}
    
    def __init__(self):
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
            
        if "from conversations" in statement_str:
            # We just need to return a conversation if requested by id
            for cid, c in self.conversations.items():
                if f"conversations.id = {cid}" in statement_str:
                    c.messages = [m for m in self.messages.values() if m.conversation_id == cid]
                    return MockResult([c])
            return MockResult([])
            
        if "from messages" in statement_str:
            for mid, m in self.messages.items():
                if f"messages.id = {mid}" in statement_str:
                    return MockResult([m])
            return MockResult([])

        if "from feedback" in statement_str:
            return MockResult([])
            
        return MockResult([])

    def add(self, instance):
        if isinstance(instance, Conversation):
            instance.id = len(self.conversations) + 1
            self.conversations[instance.id] = instance
        elif isinstance(instance, Message):
            instance.id = len(self.messages) + 1
            self.messages[instance.id] = instance

    async def commit(self):
        pass

    async def flush(self):
        pass

async def override_get_db():
    yield MockSession()

from app.api.deps import get_current_active_user

async def override_get_current_user():
    return User(
        id=2,
        name="Student User",
        email="student@college.edu",
        role=RoleEnum.student,
        is_active=True
    )

@pytest.fixture
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
async def async_client(override_dependencies):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def student_token_headers():
    return {"Authorization": "Bearer fake-token"}

from unittest.mock import AsyncMock, patch
from app.schemas.rag import RAGResponse, SourceNode

@pytest.fixture
def mock_answer_question():
    with patch("app.api.chat.answer_question") as mock:
        mock.return_value = RAGResponse(
            answer="This is a mocked RAG answer.",
            sources=[SourceNode(document_title="Mock Doc", page=1, relevance_score=0.99, document_id=1, chunk_id=1)],
            grounded=True
        )
        yield mock

@pytest.mark.asyncio
async def test_chat_new_conversation(async_client: AsyncClient, student_token_headers: dict, mock_answer_question):
    response = await async_client.post(
        "/api/chat/",
        headers=student_token_headers,
        json={"query": "What is the policy?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert "message_id" in data
    assert data["grounded"] is True or data["grounded"] is False

@pytest.mark.asyncio
async def test_chat_existing_conversation(async_client: AsyncClient, student_token_headers: dict, mock_answer_question):
    # Create conversation
    res1 = await async_client.post(
        "/api/chat/",
        headers=student_token_headers,
        json={"query": "Hello"}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    conv_id = data1["conversation_id"]
    
    # Follow up
    res2 = await async_client.post(
        "/api/chat/",
        headers=student_token_headers,
        json={
            "query": "What did I just say?",
            "conversation_id": conv_id
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["conversation_id"] == conv_id

@pytest.mark.asyncio
async def test_chat_feedback(async_client: AsyncClient, student_token_headers: dict, mock_answer_question):
    res = await async_client.post(
        "/api/chat/",
        headers=student_token_headers,
        json={"query": "Hello"}
    )
    data = res.json()
    msg_id = data["message_id"]
    
    # Submit feedback
    feedback_res = await async_client.post(
        f"/api/chat/{msg_id}/feedback",
        headers=student_token_headers,
        json={"is_helpful": True, "feedback_text": "Great answer"}
    )
    assert feedback_res.status_code == 200
    assert feedback_res.json()["status"] == "success"

@pytest.mark.asyncio
async def test_chat_contextual_request(async_client: AsyncClient, student_token_headers: dict, mock_answer_question):
    """Test Ask Nexora contextual chat request (e.g. attendance, marks, fees)."""
    response = await async_client.post(
        "/api/chat/",
        headers=student_token_headers,
        json={
            "query": "How is my attendance?",
            "context_type": "attendance"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert mock_answer_question.called

@pytest.mark.asyncio
async def test_chat_endpoint_provider_error_handling(async_client: AsyncClient, student_token_headers: dict):
    """Test that chat endpoint handles RuntimeError from provider cleanly with HTTP 503."""
    with patch("app.api.chat.answer_question", side_effect=RuntimeError("AI provider is currently unavailable. Please try again later.")):
        response = await async_client.post(
            "/api/chat/",
            headers=student_token_headers,
            json={"query": "Hello"}
        )
        assert response.status_code == 503
        assert "AI provider is currently unavailable" in response.json()["detail"]
        assert "sk-" not in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_unauthenticated(async_client: AsyncClient):
    """Test that sending a chat request without an Authorization header returns HTTP 401 Not authenticated."""
    app.dependency_overrides.pop(get_current_active_user, None)
    try:
        response = await async_client.post(
            "/api/chat",
            json={"query": "Hello without token"}
        )
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    finally:
        app.dependency_overrides[get_current_active_user] = override_get_current_user
