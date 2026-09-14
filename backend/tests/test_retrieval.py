import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.retrieval_service import retrieve_relevant_chunks
from app.models.user import User
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk

@pytest.mark.asyncio
async def test_retrieval_rbac_student():
    # Setup mock user
    student_user = User(id=1, role="student")
    
    # Setup mock db session
    mock_db = AsyncMock()
    mock_result = MagicMock()
    
    # Mocking rows: chunk, distance, document
    mock_doc = Document(id=10, title="Public Doc", status=DocumentStatusEnum.approved, visibility_scope="public")
    mock_chunk = DocumentChunk(chunk_text="Some text", page_number=1, metadata_json={"category": "test"})
    
    # .all() returns a list of tuples for joined queries
    mock_result.all.return_value = [(mock_chunk, 0.1, mock_doc)]
    mock_db.execute.return_value = mock_result
    
    # Test
    with patch("app.services.retrieval_service.get_embedding_service") as mock_get_service:
        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = [0.1] * 1536
        mock_get_service.return_value = mock_embed_service
        
        results = await retrieve_relevant_chunks("test query", student_user, mock_db)
        
        assert len(results) == 1
        assert results[0]["chunk_text"] == "Some text"
        assert results[0]["document_title"] == "Public Doc"
        assert results[0]["relevance_score"] == 0.9  # 1.0 - 0.1
        
        # Verify the query string contained the RBAC filters
        # We can inspect the arguments passed to execute
        call_args = mock_db.execute.call_args[0][0]
        # Compile the statement to string
        sql_str = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        
        # Student should only see approved and public docs
        assert "documents.status = 'approved'" in sql_str
        assert "documents.visibility_scope = 'public'" in sql_str

@pytest.mark.asyncio
async def test_retrieval_rbac_faculty():
    faculty_user = User(id=2, role="faculty")
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute.return_value = mock_result
    
    with patch("app.services.retrieval_service.get_embedding_service") as mock_get_service:
        mock_embed_service = AsyncMock()
        mock_embed_service.generate_embedding.return_value = [0.1] * 1536
        mock_get_service.return_value = mock_embed_service
        
        await retrieve_relevant_chunks("test query", faculty_user, mock_db, department_id=5, category="Syllabus")
        
        call_args = mock_db.execute.call_args[0][0]
        sql_str = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        
        # Faculty sees public and internal
        assert "documents.visibility_scope IN ('public', 'internal')" in sql_str
        # Verify metadata filters applied
        assert "documents.department_id = 5" in sql_str
        assert "documents.category = 'Syllabus'" in sql_str
