import socket
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from app.core.config import settings, normalize_database_url

raw_db_url = settings.DATABASE_URL

def is_db_host_resolvable(url: str) -> bool:
    if not url or "sqlite" in url:
        return True
    try:
        if "@" in url:
            host_part = url.split("@")[1].split("/")[0]
            host = host_part.split(":")[0].split("?")[0]
            if host and host not in ("localhost", "127.0.0.1"):
                socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False
    except Exception:
        return True

if not is_db_host_resolvable(raw_db_url):
    print("WARNING: Configured DATABASE_URL host is unresolvable. Falling back to local SQLite database.")
    DATABASE_URL = "sqlite+aiosqlite:///./nexora.db"
else:
    DATABASE_URL = normalize_database_url(raw_db_url)

if "sqlite" in DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
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

