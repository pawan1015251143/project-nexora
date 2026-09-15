from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from sqlalchemy import text
from app.db.database import engine, Base
import app.models  # Ensure all models are registered on Base.metadata

app = FastAPI(
    title="Nexora API",
    description="AI-Powered Intelligent College Assistant API",
    version="1.0.0"
)

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.on_event("startup")
async def startup_db_tables():
    """Ensure database tables exist on startup."""
    try:
        async with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Startup database initialization warning: {e}")

# CORS — configured via CORS_ORIGINS environment variable + automatic Vercel/Local regex fallback
origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, documents, chat, notices, search, analytics, student, notice_inbox

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(notices.router, prefix="/api/notices", tags=["Notices"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(notice_inbox.router, prefix="/api/admin/notice-inbox", tags=["Admin Notice Inbox"])


@app.get("/")
async def root():
    return {"message": "Welcome to Nexora API"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "nexora-backend", "version": "1.0.0"}


@app.get("/api/health")
async def api_health_check():
    return {"status": "ok", "service": "nexora-backend", "version": "1.0.0"}
