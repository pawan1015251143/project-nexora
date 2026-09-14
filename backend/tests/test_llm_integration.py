import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.rag_service import answer_question
from app.schemas.rag import RAGRequest
from app.models.user import User
from app.services.llm_service import (
    get_llm_service,
    MockLLMService,
    OpenAILLMService,
)
from app.core.config import settings


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


# --- 1. Provider Selection Tests ---

def test_get_llm_service_provider_selection():
    """Test get_llm_service correctly selects MockLLMService or OpenAILLMService based on LLM_PROVIDER setting."""
    with patch.object(settings, "LLM_PROVIDER", "mock"):
        service = get_llm_service()
        assert isinstance(service, MockLLMService)

    with patch.object(settings, "LLM_PROVIDER", "openai"), patch.object(settings, "OPENAI_API_KEY", "sk-fake-test-key"):
        service = get_llm_service()
        assert isinstance(service, OpenAILLMService)


# --- 2. Mock LLM Service Tests ---

@pytest.mark.asyncio
async def test_mock_llm_service_behavior():
    """Verify MockLLMService generate_response, translate_notice, and extract_notice_info functions."""
    service = MockLLMService()

    # Grounded response
    ans, grounded = await service.generate_response("Sys prompt", "Tell me about exams")
    assert grounded is True
    assert "mocked answer" in ans.lower()

    # Irrelevant response
    ans_irrel, grounded_irrel = await service.generate_response("Sys prompt", "irrelevant topic")
    assert grounded_irrel is False
    assert "cannot verify" in ans_irrel.lower()

    # Translation
    trans = await service.translate_notice("Final Exams Notice", mode="hi_full")
    assert trans == "(Mocked Hindi Translation)"

    # Notice Extraction
    extracted = await service.extract_notice_info("Exams scheduled for next week")
    assert "title" in extracted
    assert extracted["notice_type"] == "General"


# --- 3. OpenAI Configuration & Missing Key Tests ---

def test_openai_service_configuration():
    """Test OpenAILLMService reads OPENAI_MODEL and handles configuration properly."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-test-key"), \
         patch.object(settings, "OPENAI_MODEL", "gpt-4o-mini"):
        service = OpenAILLMService()
        assert service.model == "gpt-4o-mini"
        assert service.client is not None


@pytest.mark.asyncio
async def test_openai_service_missing_api_key():
    """Test OpenAILLMService when OPENAI_API_KEY is missing or empty."""
    with patch.object(settings, "OPENAI_API_KEY", None):
        service = OpenAILLMService()
        assert service.client is None

        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_response("System prompt", "User query")
        assert "AI provider is currently unavailable" in str(exc_info.value)
        assert "sk-" not in str(exc_info.value)


# --- 4. OpenAI Provider Mocked Calls & Success ---

@pytest.mark.asyncio
async def test_openai_service_generate_response_success():
    """Test OpenAILLMService generate_response with mocked OpenAI response."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-fake-test-key"):
        service = OpenAILLMService()

        mock_choice = MagicMock()
        mock_choice.message.content = "Library opens at 8 AM according to document."
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        service.client = MagicMock()
        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        ans, grounded = await service.generate_response("System prompt", "When does library open?")
        assert ans == "Library opens at 8 AM according to document."
        assert grounded is True


@pytest.mark.asyncio
async def test_openai_service_ungrounded_response():
    """Test OpenAILLMService detects ungrounded response."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-fake-test-key"):
        service = OpenAILLMService()

        mock_choice = MagicMock()
        mock_choice.message.content = "I cannot verify the information based on the provided context."
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        service.client = MagicMock()
        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        ans, grounded = await service.generate_response("System prompt", "Unrelated query")
        assert grounded is False


# --- 5. OpenAI Error & Timeout Handling ---

@pytest.mark.asyncio
async def test_openai_service_timeout_handling():
    """Test OpenAILLMService timeout handling raises user-friendly RuntimeError."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-fake-test-key"):
        service = OpenAILLMService()

        service.client = MagicMock()
        service.client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_response("Sys", "User")
        assert "AI provider is currently unavailable" in str(exc_info.value)
        assert "TimeoutError" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_service_api_error_handling():
    """Test OpenAILLMService handles OpenAI exceptions (Authentication, Rate Limit, Connection)."""
    import openai

    with patch.object(settings, "OPENAI_API_KEY", "sk-fake-test-key"):
        service = OpenAILLMService()
        service.client = MagicMock()

        # Mock APIConnectionError
        service.client.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=MagicMock())
        )
        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_response("Sys", "User")
        assert "AI provider is currently unavailable" in str(exc_info.value)

        # Mock AuthenticationError
        mock_response = MagicMock()
        mock_response.status_code = 401
        service.client.chat.completions.create = AsyncMock(
            side_effect=openai.AuthenticationError(
                message="Incorrect API key provided",
                response=mock_response,
                body={"error": {"message": "Incorrect API key provided"}}
            )
        )
        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_response("Sys", "User")
        assert "AI provider is currently unavailable" in str(exc_info.value)
        assert "Incorrect API key" not in str(exc_info.value)


# --- 6. RAG Pipeline Error & History Integration ---

@patch("app.services.rag_service.retrieve_relevant_chunks")
@pytest.mark.asyncio
async def test_llm_provider_timeout_in_rag(mock_retrieve, mock_db, user):
    mock_retrieve.return_value = [make_chunk("Valid Doc", 1, 0.95)]
    req = RAGRequest(query="TIMEOUT_SIMULATION")

    with pytest.raises(RuntimeError) as exc_info:
        await answer_question(req, user, mock_db)

    assert "AI provider is currently unavailable" in str(exc_info.value)
    assert "TimeoutError" not in str(exc_info.value)


@patch("app.services.rag_service.retrieve_relevant_chunks")
@pytest.mark.asyncio
async def test_conversation_history_passed(mock_retrieve, mock_db, user):
    mock_retrieve.return_value = [make_chunk("Valid Doc", 1, 0.95)]
    history = [{"role": "user", "content": "What is the history?"}, {"role": "assistant", "content": "It is this."}]
    req = RAGRequest(query="Normal question", conversation_history=history)

    res = await answer_question(req, user, mock_db)

    assert res.grounded is True
    assert "mocked answer" in res.answer.lower()
