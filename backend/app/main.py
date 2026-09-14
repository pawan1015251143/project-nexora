from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Nexora API",
    description="AI-Powered Intelligent College Assistant API",
    version="1.0.0"
)

# CORS — configured via CORS_ORIGINS environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
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
