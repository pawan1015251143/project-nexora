import logging
import traceback
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document, DocumentStatusEnum
from app.models.document_chunk import DocumentChunk
import os
import re
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

# Configurable chunking settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def clean_text(text: str) -> str:
    """Clean unnecessary whitespace from text."""
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with double newline to preserve paragraph boundaries
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text_from_txt(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from a TXT file. Treats the entire file as page 1."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    text = clean_text(text)
    if not text:
        return []
        
    return [{"page_number": 1, "text": text}]

def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from a PDF file preserving page numbers."""
    pages_data = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            cleaned_text = clean_text(text)
            if cleaned_text:
                # fitz is 0-indexed, human pages are 1-indexed
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": cleaned_text
                })
    finally:
        doc.close()
    return pages_data

async def chunk_pages_data(pages_data: List[Dict[str, Any]], metadata_base: Dict[str, Any]) -> List[DocumentChunk]:
    """Split extracted page text into semantic chunks and prepare DB objects with embeddings."""
    
    # We use character splitter since tiktoken is not available on Python 3.14
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    raw_chunks = []
    
    for page_info in pages_data:
        page_num = page_info["page_number"]
        page_text = page_info["text"]
        
        # Split text into chunks
        text_chunks = text_splitter.split_text(page_text)
        for chunk_text in text_chunks:
            raw_chunks.append({
                "text": chunk_text,
                "page_number": page_num
            })
            
    if not raw_chunks:
        return []
        
    # Generate embeddings in batch
    embed_service = get_embedding_service()
    texts_to_embed = [c["text"] for c in raw_chunks]
    embeddings = await embed_service.generate_embeddings(texts_to_embed)
    
    chunks_to_insert = []
    
    for chunk_index, (chunk_data, embedding) in enumerate(zip(raw_chunks, embeddings)):
        # Add specific chunk metadata
        chunk_meta = metadata_base.copy()
        chunk_meta["page_number"] = chunk_data["page_number"]
        chunk_meta["chunk_index"] = chunk_index
        
        # Create DB object
        chunk = DocumentChunk(
            document_id=metadata_base["document_id"],
            chunk_text=chunk_data["text"],
            page_number=chunk_data["page_number"],
            chunk_index=chunk_index,
            metadata_json=chunk_meta,
            embedding=embedding
        )
        chunks_to_insert.append(chunk)
            
    return chunks_to_insert

async def process_document(document_id: int, db: AsyncSession):
    """
    Background task to process a document:
    1. Extract text
    2. Clean text
    3. Split into semantic chunks
    4. Generate embeddings
    5. Store chunks
    """
    # 1. Fetch document
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    
    if not doc:
        logger.error(f"Document {document_id} not found for processing.")
        return
        
    try:
        # Update status to processing if not already
        if doc.status != DocumentStatusEnum.processing:
            doc.status = DocumentStatusEnum.processing
            await db.commit()
            
        file_path = doc.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist on disk.")
            
        # 2. Extract text based on mime_type
        pages_data = []
        ext = os.path.splitext(file_path)[1].lower()
        if doc.mime_type == "application/pdf" or ext == ".pdf":
            pages_data = extract_text_from_pdf(file_path)
        elif doc.mime_type == "text/plain" or ext == ".txt":
            pages_data = extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported mime_type for processing: {doc.mime_type}")
            
        if not pages_data:
            raise ValueError("No text could be extracted from the document.")
            
        # 3. Chunk text & generate embeddings
        metadata_base = {
            "document_id": doc.id,
            "department_id": doc.department_id,
            "category": doc.category,
            "academic_year": doc.academic_year,
            "visibility_scope": doc.visibility_scope,
            "source_title": doc.title
        }
        if doc.effective_from:
            metadata_base["effective_from"] = doc.effective_from.isoformat()
            
        chunks = await chunk_pages_data(pages_data, metadata_base)
        
        # 4. Clean up old chunks (if reindexing)
        await db.execute(
            DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc.id)
        )
        
        # 5. Store new chunks
        db.add_all(chunks)
        
        # 6. Update Document Status
        doc.status = DocumentStatusEnum.ready
        doc.error_message = None
        await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        # Safe error logging
        error_msg = f"Processing failed: {str(e)[:200]}"
        
        # Rollback any pending operations (like chunk additions)
        await db.rollback()
        
        # Re-fetch document inside new transaction to update status
        result = await db.execute(select(Document).where(Document.id == document_id))
        failed_doc = result.scalars().first()
        if failed_doc:
            failed_doc.status = DocumentStatusEnum.failed
            failed_doc.error_message = error_msg
            await db.commit()
