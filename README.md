# Nexora: Intelligent College Assistant 🎓

Nexora is an AI-powered college assistant designed to streamline document management, student inquiries, and administrative workflows. Leveraging Retrieval-Augmented Generation (RAG), Nexora provides instant, context-aware answers directly from institutional documents, alongside a suite of management tools for students, faculty, and administrators.

## 🌟 Features

- **AI-Powered Q&A:** Chat with college documents using advanced RAG and vector search.
- **Role-Based Access Control (RBAC):** Distinct interfaces and permissions for Students, Faculty, and Admins.
- **Document Management:** Securely upload, process, and query institutional PDFs and text files.
- **Notices System:** Broadcast important updates to specific departments or the entire college.
- **Analytics Dashboard:** Visualize usage, queries, user engagement, and system metrics.
- **Dark Mode:** A polished, fully responsive UI with seamless theme switching.

## 🏗 Architecture

Nexora is built on a modern, decoupled architecture:
1. **Frontend:** A React Single Page Application (SPA) built with Vite, utilizing Tailwind CSS for styling and Recharts for analytics.
2. **Backend:** A high-performance Python FastAPI server handling authentication, routing, and orchestrating the AI logic.
3. **Database:** PostgreSQL enriched with the `pgvector` extension for efficient semantic search and high-dimensional vector embeddings.
4. **AI/LLM Layer:** Integrates with OpenAI (or alternative providers) for both embedding generation and conversational synthesis.

## 🛠 Tech Stack

**Frontend:**
- React 18, TypeScript, Vite
- Tailwind CSS (v4), Lucide React
- React Router DOM
- Recharts, React Markdown

**Backend:**
- Python 3.10+, FastAPI, Uvicorn
- SQLAlchemy (Async), asyncpg, Alembic
- PyMuPDF (PDF Processing), LangChain Text Splitters
- Passlib, Bcrypt, PyJWT (Authentication)

**Database:**
- PostgreSQL
- `pgvector` extension

## 📁 Folder Structure

```text
nexora/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/                  
│   │   ├── api/              # API Route definitions
│   │   ├── core/             # Core configurations (env, auth)
│   │   ├── db/               # Database connection and session management
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── security/         # JWT and password hashing utilities
│   │   └── services/         # Business logic (AI, Embeddings, Document processing)
│   ├── tests/                # Pytest integration suite
│   ├── .env.example          # Backend environment variables
│   ├── Dockerfile            # Container definition
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── public/               # Static assets
    ├── src/
    │   ├── api/              # API client configurations
    │   ├── components/       # Reusable UI components
    │   ├── lib/              # Utility functions
    │   └── pages/            # View components (Dashboards, Chat, etc.)
    ├── .env.example          # Frontend environment variables
    ├── index.html            # Entry point
    └── package.json          # Node dependencies
```

## 📋 Prerequisites

Ensure you have the following installed before running the project:
- **Node.js** (v18+)
- **Python** (v3.10+)
- **PostgreSQL** (v15+) with `pgvector` extension

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nexora.git
   cd nexora
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

3. **Backend Setup:**
   ```bash
   cd ../backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 🔐 Environment Variables

You need to set up environment variables for both the frontend and backend. 
Reference `.env.example` in both directories.

**Backend (`backend/.env`):**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nexora_db
SECRET_KEY=your_super_secret_jwt_key
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
OPENAI_API_KEY=sk-your-openai-api-key
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
```

**Frontend (`frontend/.env`):**
```env
VITE_API_URL=http://localhost:8000
```

## 🗄 Database & pgvector Setup

Nexora relies on `pgvector` to store and query document embeddings. 
1. Install PostgreSQL and create a database (e.g., `nexora_db`).
2. Log into your database and enable the extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run the backend migrations to create the schema:
   ```bash
   cd backend
   alembic upgrade head
   ```

## 🚀 Running Locally

You need to run both the frontend and backend servers simultaneously.

**Start the Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Start the Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser.

## 🧪 Running Tests

The backend contains a comprehensive suite of integration tests.
```bash
cd backend
source venv/bin/activate
python -m pytest tests/
```

## 🧠 Document Ingestion & RAG Explanation

**Retrieval-Augmented Generation (RAG):**
When a user asks a question, Nexora doesn't just rely on the LLM's base knowledge. Instead, it:
1. Converts the user's question into a numerical vector (embedding).
2. Performs a similarity search in PostgreSQL using `pgvector` to find the most relevant document chunks.
3. Injects those specific chunks into the LLM prompt.
4. Generates a precise, highly-contextualized response citing the original source.

**Ingestion Pipeline:**
When an Admin uploads a PDF/TXT document:
- **PyMuPDF** parses the raw text.
- **LangChain** text splitters recursively chunk the text into semantically cohesive blocks.
- **OpenAI** generates vector embeddings for each chunk.
- Chunks and metadata are persisted in the `DocumentChunk` table.

## 🌍 Deployment

**Backend (Render / Fly.io / Railway):**
1. Use the provided `Dockerfile`.
2. Supply the required environment variables (including the production `DATABASE_URL`).
3. Expose port `8000`.

**Database (Supabase / Neon):**
Managed PostgreSQL providers support `pgvector` by default. Execute the `CREATE EXTENSION` command via their SQL editor, update your `DATABASE_URL`, and run `alembic upgrade head`.

**Frontend (Vercel / Netlify):**
Point Vercel to the `frontend/` directory. Set `VITE_API_URL` to your deployed backend URL. Vercel will automatically run `npm run build`.

## 🛡 Security Notes

- **Password Hashing:** Handled securely via `passlib` (using `bcrypt==3.2.2`).
- **JWT Authorization:** Tokens are short-lived. Role-based guards prevent lateral privilege escalation.
- **Data Isolation:** Private documents are strictly partitioned by Role and Department. 
- **Prompt Injection:** RAG context is strictly structured. However, in production, consider adding an LLM firewall (like NeMo Guardrails) for strict output parsing.
- **CORS:** Ensure `CORS_ORIGINS` is strictly defined in your production `.env` to prevent cross-site exploitation.

## 🖼 Screenshots

*(Add screenshots here)*
- `[Screenshot: Dashboard]`
- `[Screenshot: AI Chat Interface]`
- `[Screenshot: Document Upload Flow]`
- `[Screenshot: Analytics]`

## 🔑 Demo Credentials

*(Optional: Provide demo credentials if hosting a public showcase)*
- **Admin:** `admin@college.edu` / `adminpass`
- **Faculty:** `faculty@college.edu` / `facultypass`
- **Student:** `student@college.edu` / `studentpass`

## 🔮 Future Improvements
- Add WebSocket support for real-time streaming AI responses.
- Implement rate limiting (e.g., `slowapi`) to protect LLM endpoints from abuse.
- Support local LLMs (e.g., Llama 3 via Ollama) to reduce OpenAI API costs.
- Integrate OCR pipelines for scanned image PDFs.
