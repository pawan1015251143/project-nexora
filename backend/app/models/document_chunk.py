from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    
    # Using 1536 dimensions as default for OpenAI text-embedding-3-small
    # Adjust this if using a different embedding model
    embedding = Column(Vector(1536), nullable=True)
    
    metadata_json = Column(JSONB, nullable=True)

    document = relationship("Document", back_populates="chunks")
