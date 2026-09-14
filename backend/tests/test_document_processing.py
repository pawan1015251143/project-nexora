import pytest
import os
import io
import fitz # PyMuPDF
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk
from app.services.document_processor import (
    clean_text, 
    extract_text_from_txt, 
    extract_text_from_pdf,
    process_document
)

# A fake AsyncSession for testing just the processor
class FakeResult:
    def __init__(self, data):
        self._data = data
    def scalars(self):
        class FakeScalars:
            def __init__(self, data):
                self._data = data
            def first(self):
                return self._data[0] if self._data else None
            def all(self):
                return self._data
        return FakeScalars(self._data)

class FakeSession:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.doc = None
    
    async def execute(self, query):
        q_str = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
        if "from documents" in q_str:
            if self.doc:
                return FakeResult([self.doc])
            return FakeResult([])
        if "delete from document_chunks" in q_str:
            return FakeResult([])
        return FakeResult([])

    def add_all(self, instances):
        self.added.extend(instances)

    async def commit(self):
        pass

    async def rollback(self):
        self.added = []


def test_clean_text():
    raw = "This   is   spaced. \n\n\n\n Paragraph 2."
    cleaned = clean_text(raw)
    assert cleaned == "This is spaced. \n\n Paragraph 2."

def test_extract_txt(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("Hello world")
    res = extract_text_from_txt(str(p))
    assert len(res) == 1
    assert res[0]["text"] == "Hello world"
    assert res[0]["page_number"] == 1

def test_extract_pdf(tmp_path):
    # Create a simple PDF using fitz
    p = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "PDF Test Page 1")
    doc.save(str(p))
    doc.close()

    res = extract_text_from_pdf(str(p))
    assert len(res) == 1
    assert "PDF Test Page 1" in res[0]["text"]
    assert res[0]["page_number"] == 1

@pytest.mark.asyncio
async def test_process_document_success(tmp_path):
    # Create a TXT document to process
    p = tmp_path / "doc.txt"
    # Make it long enough to be chunked if we set small chunk sizes, but here we just test standard execution
    text = "A" * 1500 
    p.write_text(text)
    
    doc = Document(
        id=1,
        title="Test Doc",
        file_path=str(p),
        mime_type="text/plain",
        file_size=1500,
        department_id=1,
        category="Policy",
        visibility_scope="public",
        status=DocumentStatusEnum.uploaded
    )
    
    session = FakeSession()
    session.doc = doc
    
    await process_document(1, session)
    
    assert doc.status == DocumentStatusEnum.ready
    assert doc.error_message is None
    
    # Check chunks
    assert len(session.added) > 0
    chunk = session.added[0]
    assert isinstance(chunk, DocumentChunk)
    assert chunk.document_id == 1
    assert chunk.metadata_json["category"] == "Policy"
    
@pytest.mark.asyncio
async def test_process_document_file_not_found():
    doc = Document(
        id=2,
        file_path="nonexistent.txt",
        mime_type="text/plain",
        status=DocumentStatusEnum.uploaded
    )
    session = FakeSession()
    session.doc = doc
    
    await process_document(2, session)
    
    assert doc.status == DocumentStatusEnum.failed
    assert "does not exist on disk" in doc.error_message
