from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List


def normalize_database_url(url: str) -> str:
    """
    Ensure the database URL uses the asyncpg driver for PostgreSQL with AsyncEngine.

    Transforms:
        postgresql://... -> postgresql+asyncpg://...
        postgres://...   -> postgresql+asyncpg://...
    Preserves:
        postgresql+asyncpg://... (unchanged)
        Query parameters such as ?pgbouncer=true, sslmode, etc.
    """
    if not url:
        return url
    url = url.strip().strip("'\"")
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    return url


class Settings(BaseSettings):
    # AI/LLM providers
    EMBEDDING_PROVIDER: str = "mock"   # "mock" | "openai"
    LLM_PROVIDER: str = "mock"         # "mock" | "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

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

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            return normalize_database_url(v)
        return v

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS env var into a list, stripping whitespace and trailing slashes."""
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

