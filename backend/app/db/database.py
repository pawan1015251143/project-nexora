from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from app.core.config import settings, normalize_database_url

DATABASE_URL = normalize_database_url(settings.DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,   # Set True only for local debugging; verbose in production logs
    pool_pre_ping=True,  # Detect stale connections
    pool_size=10,
    max_overflow=20,
)


@event.listens_for(engine.sync_engine, "do_connect")
def _receive_do_connect(dialect, conn_rec, cargs, cparams):
    """
    Ensure compatibility with Supabase PgBouncer pooler and asyncpg.
    - If ?pgbouncer=true was in the URL, remove it from connect keyword args
      to avoid asyncpg TypeError (connect() unexpected keyword argument).
    - Disable prepared statement cache for transaction pooler mode (port 6543).
    """
    is_pgbouncer = cparams.pop("pgbouncer", None) is not None
    host = str(cparams.get("host", ""))
    port = cparams.get("port")
    if is_pgbouncer or "pooler.supabase.com" in host or port == 6543:
        cparams["statement_cache_size"] = 0


AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
async_session_maker = AsyncSessionLocal

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

