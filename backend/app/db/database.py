import socket
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from app.core.config import settings, normalize_database_url

raw_db_url = settings.DATABASE_URL.strip().strip("'\"")

def extract_host(url: str) -> str:
    if "@" in url:
        part = url.split("@")[1].split("/")[0]
        return part.split(":")[0].split("?")[0]
    return ""

host_to_check = extract_host(raw_db_url)
use_sqlite = False

if "sqlite" in raw_db_url:
    use_sqlite = True
elif host_to_check and host_to_check not in ("localhost", "127.0.0.1"):
    try:
        socket.getaddrinfo(host_to_check, None)
    except Exception as e:
        print(f"WARNING: Host '{host_to_check}' in DATABASE_URL cannot be resolved ({e}). Falling back to SQLite.")
        use_sqlite = True

if use_sqlite:
    DATABASE_URL = "sqlite+aiosqlite:///./nexora.db"
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    DATABASE_URL = normalize_database_url(raw_db_url)
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
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

