from typing import List
from abc import ABC, abstractmethod
import random
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseEmbeddingService(ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
        
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding."""
        pass

class MockEmbeddingService(BaseEmbeddingService):
    """A mock service that generates random vectors for local testing without an API key."""
    
    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # In a real mock, we might want deterministic output, but random is fine for schema tests
        return [[random.uniform(-1.0, 1.0) for _ in range(self.dimensions)] for _ in texts]

    async def generate_embedding(self, text: str) -> List[float]:
        return [random.uniform(-1.0, 1.0) for _ in range(self.dimensions)]

class OpenAIEmbeddingService(BaseEmbeddingService):
    """Service utilizing the official OpenAI API."""
    
    def __init__(self):
        try:
            from openai import AsyncOpenAI
            if not settings.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY not found. OpenAI calls will fail.")
                
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "text-embedding-3-small"
        except ImportError:
            logger.error("OpenAI package not installed.")
            self.client = None

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
            
        # Handle large batches if necessary, but assume lists are reasonably sized here
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        # response.data is a list of Embedding objects, ordered by input
        return [item.embedding for item in response.data]

    async def generate_embedding(self, text: str) -> List[float]:
        res = await self.generate_embeddings([text])
        return res[0]

def get_embedding_service() -> BaseEmbeddingService:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai":
        return OpenAIEmbeddingService()
    else:
        return MockEmbeddingService()
