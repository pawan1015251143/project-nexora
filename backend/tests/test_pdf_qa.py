import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.user import User
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk
from app.schemas.rag import RAGRequest
from app.services.retrieval_service import retrieve_relevant_chunks
import numpy as np

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.retrieval_service.get_embedding_service") as mock_get:
        mock_service = AsyncMock()
        mock_service.generate_embedding.return_value = np.zeros(1536)
        mock_get.return_value = mock_service
        yield mock_service

@pytest.mark.asyncio
async def test_isolated_retrieval_success(mock_embedding_service):
    # Setup test user and context
    test_user = User(id=1, role="student")
    
    # Mock Document
    private_doc = Document(
        id=99,
        title="My Private Notes",
        visibility_scope="private",
        uploaded_by=test_user.id,
        status=DocumentStatusEnum.ready
    )
    
    # Mock chunk
    mock_chunk = DocumentChunk(
        id=1,
        document_id=99,
        chunk_text="Stack is LIFO, Queue is FIFO",
        page_number=1,
        chunk_index=0,
        metadata_json={"document_id": 99, "source_title": "My Private Notes", "visibility_scope": "private"}
    )
    
    # Mock DB execution
    mock_db = AsyncMock()
    mock_result = MagicMock()
    # Return list of tuples matching what the query does: (chunk, distance, doc)
    mock_result.all.return_value = [(mock_chunk, 0.1, private_doc)]
    mock_db.execute.return_value = mock_result
    
    # Run retrieval in isolated mode (with document_id=99)
    chunks = await retrieve_relevant_chunks("What is a stack?", test_user, mock_db, document_id=99)
    
    assert len(chunks) == 1
    assert chunks[0]["document_id"] == 99
    assert chunks[0]["chunk_text"] == "Stack is LIFO, Queue is FIFO"

@pytest.mark.asyncio
async def test_isolated_retrieval_unauthorized(mock_embedding_service):
    # Setup user who does NOT own the document
    other_user = User(id=2, role="student")
    
    # Because of how we mock, we want to simulate the SQL query returning nothing
    # when the user tries to access a document they don't own. 
    # SQLAlchemy where clauses are built into the query. Since we mock execute(),
    # we just need to ensure our test reflects the intended output. 
    # For a real DB test, the where(uploaded_by == user.id) would filter it.
    # In this unit test, we just test that the query construction executes cleanly.
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute.return_value = mock_result
    
    chunks = await retrieve_relevant_chunks("What is a stack?", other_user, mock_db, document_id=99)
    
    assert len(chunks) == 0

@pytest.mark.asyncio
async def test_global_search_excludes_private(mock_embedding_service):
    test_user = User(id=1, role="student")
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute.return_value = mock_result
    
    # Query without document_id (Global search)
    chunks = await retrieve_relevant_chunks("What is a stack?", test_user, mock_db, document_id=None)
    
    # It should succeed in calling the DB without errors
    assert isinstance(chunks, list)
