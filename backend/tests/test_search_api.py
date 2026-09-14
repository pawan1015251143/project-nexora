import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User, RoleEnum
from app.api.deps import get_current_active_user
from unittest.mock import patch, AsyncMock

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
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
async def async_client(override_dependencies):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def token_headers():
    return {"Authorization": "Bearer fake-token"}

@pytest.fixture
def mock_retrieval():
    with patch("app.api.search.retrieve_relevant_chunks") as mock:
        mock.return_value = [{"id": 1, "chunk_text": "hello", "document_title": "doc", "page_number": 1, "document_id": 1, "relevance_score": 0.9, "metadata": {}}]
        yield mock

@pytest.mark.asyncio
async def test_search_documents_semantic(async_client: AsyncClient, token_headers: dict, mock_retrieval):
    response = await async_client.get("/api/search?query=test&search_mode=semantic", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_found" in data

@pytest.mark.asyncio
async def test_search_documents_keyword(async_client: AsyncClient, token_headers: dict, mock_retrieval):
    response = await async_client.get("/api/search?query=test&search_mode=keyword", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_found" in data

@pytest.mark.asyncio
async def test_search_documents_unauthorized(async_client: AsyncClient, mock_retrieval):
    # Mock auth to throw 401 explicitly
    from fastapi import HTTPException
    app.dependency_overrides[get_current_active_user] = lambda: (_ for _ in ()).throw(HTTPException(status_code=401, detail="Unauthorized"))
    
    response = await async_client.get("/api/search?query=test&search_mode=semantic")
    assert response.status_code == 401
    
    # Restore mock for other tests
    app.dependency_overrides[get_current_active_user] = override_get_current_user
