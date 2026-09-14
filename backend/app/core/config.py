from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    # AI/LLM providers
    EMBEDDING_PROVIDER: str = "mock"   # "mock" | "openai"
    LLM_PROVIDER: str = "mock"         # "mock" | "openai"
    OPENAI_API_KEY: Optional[str] = None

    # Database (also consumed directly by database.py via os.getenv for compatibility)
    DATABASE_URL: str = "postgresql+asyncpg://nexora_user:nexora_password@localhost:5432/nexora_db"

    # JWT
    SECRET_KEY: str = "supersecretkey_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS env var into a list, stripping whitespace."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
