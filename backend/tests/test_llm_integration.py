import pytest
from unittest.mock import AsyncMock, patch
from app.services.rag_service import answer_question
from app.schemas.rag import RAGRequest
from app.models.user import User

def make_chunk(title: str, doc_id: int, score: float, text: str = "Test content"):
    return {
        "document_title": title,
        "document_id": doc_id,
        "page_number": 1,
        "relevance_score": score,
        "chunk_text": text
    }

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def user():
    return User(id=1, role="student")

@patch("app.services.rag_service.retrieve_relevant_chunks")
@pytest.mark.asyncio
async def test_llm_provider_timeout(mock_retrieve, mock_db, user):
    mock_retrieve.return_value = [make_chunk("Valid Doc", 1, 0.95)]
    # Use the trigger word for our mock LLM to simulate a timeout/error
    req = RAGRequest(query="TIMEOUT_SIMULATION")
    
    with pytest.raises(RuntimeError) as exc_info:
        await answer_question(req, user, mock_db)
        
    assert "AI provider is currently unavailable" in str(exc_info.value)
    # Ensure raw API errors/timeouts aren't leaked
    assert "TimeoutError" not in str(exc_info.value)

@patch("app.services.rag_service.retrieve_relevant_chunks")
@pytest.mark.asyncio
async def test_llm_provider_api_error(mock_retrieve, mock_db, user):
    mock_retrieve.return_value = [make_chunk("Valid Doc", 1, 0.95)]
    req = RAGRequest(query="API_ERROR_SIMULATION")
    
    with pytest.raises(RuntimeError) as exc_info:
        await answer_question(req, user, mock_db)
        
    assert "AI provider is currently unavailable" in str(exc_info.value)
    
@patch("app.services.rag_service.retrieve_relevant_chunks")
@pytest.mark.asyncio
async def test_conversation_history_passed(mock_retrieve, mock_db, user):
    mock_retrieve.return_value = [make_chunk("Valid Doc", 1, 0.95)]
    history = [{"role": "user", "content": "What is the history?"}, {"role": "assistant", "content": "It is this."}]
    req = RAGRequest(query="Normal question", conversation_history=history)
    
    # We just ensure it doesn't crash and returns normally.
    # If the LLM service crashed due to the history argument, this would fail.
    res = await answer_question(req, user, mock_db)
    
    assert res.grounded is True
    assert "mocked answer" in res.answer.lower()
