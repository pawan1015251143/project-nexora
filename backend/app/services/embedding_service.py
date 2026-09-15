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
        self.model = "text-embedding-3-small"
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found. OpenAI embedding calls will fail.")
            self.client = None
            return

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embedding client: {e}")
            self.client = None

    def _ensure_client(self):
        if not self.client or not settings.OPENAI_API_KEY:
            logger.error("Attempted OpenAI embedding call without client or valid OPENAI_API_KEY.")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        self._ensure_client()
        try:
            import openai
            import asyncio
            response = await asyncio.wait_for(
                self.client.embeddings.create(
                    input=texts,
                    model=self.model
                ),
                timeout=15.0
            )
            return [item.embedding for item in response.data]
        except asyncio.TimeoutError:
            logger.error("Embedding Provider Timeout")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        except Exception as e:
            import openai
            if isinstance(e, (openai.OpenAIError, openai.APIError, openai.APIConnectionError, openai.RateLimitError, openai.AuthenticationError)):
                logger.error(f"Embedding API Error ({type(e).__name__}): {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")
            elif isinstance(e, RuntimeError):
                raise
            else:
                logger.error(f"Unexpected Embedding Error: {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")

    async def generate_embedding(self, text: str) -> List[float]:
        res = await self.generate_embeddings([text])
        return res[0]

def get_embedding_service() -> BaseEmbeddingService:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai":
        return OpenAIEmbeddingService()
    else:
        return MockEmbeddingService()
