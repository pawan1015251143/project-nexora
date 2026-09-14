# Nexora — Deployment Checklist

## Database Setup
- [ ] PostgreSQL database created (Supabase / Neon / Railway)
- [ ] `CREATE EXTENSION IF NOT EXISTS vector;` executed
- [ ] `alembic upgrade head` applied successfully
- [ ] All 4 migrations applied (`abc123def456` → `97aef22ba29d` → `37276a0e1820` → `b1c2d3e4f5a6`)

## Backend Deployment
- [ ] Backend environment variables configured:
  - [ ] `DATABASE_URL` — PostgreSQL connection string
  - [ ] `SECRET_KEY` — strong random 64-char hex
  - [ ] `CORS_ORIGINS` — Vercel frontend URL
  - [ ] `LLM_PROVIDER` — `openai` or `mock`
  - [ ] `EMBEDDING_PROVIDER` — `openai` or `mock`
  - [ ] `OPENAI_API_KEY` — (if using openai providers)
- [ ] Backend deployed (Render / Railway / Fly.io)
- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] `GET /api/health` returns `{"status":"ok"}`

## Frontend Deployment
- [ ] `VITE_API_URL` set in Vercel environment variables
- [ ] `VITE_API_URL` points to deployed backend (NOT localhost)
- [ ] `OPENAI_API_KEY` is NOT in Vercel environment variables
- [ ] Frontend deployed to Vercel
- [ ] `npm run build` passes with 0 TypeScript errors
- [ ] `vercel.json` present for SPA routing

## Authentication
- [ ] Register as student — works
- [ ] Register as faculty — works
- [ ] Login — JWT returned
- [ ] JWT attached to subsequent requests
- [ ] Admin login works
- [ ] Role-based access: student cannot access admin routes

## Student Features
- [ ] Student dashboard loads (attendance, marks, fees summary)
- [ ] Attendance page loads
- [ ] Marks page loads
- [ ] Fees page loads
- [ ] Notices page loads (student view, shows only published notices)
- [ ] Ask Nexora chat works for student
- [ ] Context-aware Ask Nexora (attendance/marks/fees context)

## Admin Features
- [ ] Admin dashboard loads
- [ ] Notice Inbox loads (shows demo messages)
- [ ] Notice import works (POST /api/admin/notice-inbox/{id}/import)
- [ ] AI processing works (POST /api/admin/notice-inbox/{id}/process)
- [ ] Notice approval works (POST /api/admin/notice-inbox/{id}/approve)
- [ ] Notice rejection works (POST /api/admin/notice-inbox/{id}/reject)
- [ ] Notice publication works (POST /api/admin/notice-inbox/{id}/publish)
- [ ] Published notice appears in student Notice portal
- [ ] Document manager loads
- [ ] User manager loads
- [ ] Analytics page loads

## RAG / AI
- [ ] Ask Nexora responds correctly
- [ ] Documents indexed via RAG are retrievable
- [ ] Published notices are indexed and retrievable via Ask Nexora
- [ ] AI failure returns a graceful error (not 500 crash)

## Demo Data
- [ ] Demo notices seeded: `python scripts/seed_demo_notices.py`
- [ ] Demo student data seeded (if student seed script exists)
- [ ] Seed scripts are idempotent (safe to run multiple times)

## Backend Tests
- [ ] `python -m pytest tests/ -v` → **66/66 passed**

## Final Verification
- [ ] CORS: frontend domain allowed in `CORS_ORIGINS`
- [ ] No `localhost` URLs hardcoded in production frontend build
- [ ] No secrets committed to git
- [ ] `.env` files are in `.gitignore`
- [ ] Health endpoint reachable from frontend domain
