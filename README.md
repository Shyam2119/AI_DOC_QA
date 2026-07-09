# DocMind — AI Document Q&A System

A full-stack **RAG (Retrieval-Augmented Generation)** application. Upload PDFs, ask questions, and get cited, grounded answers — powered by **LangChain + local HuggingFace models. No API key required.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3, LangChain 0.2 |
| Vector Store | FAISS (local, no extra service) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, HuggingFace) |
| QA Model | `deepset/tinyroberta-squad2` (local, extractive QA) |
| PDF Processing | LangChain `PyPDFLoader` |
| Database | MySQL 8 + SQLAlchemy + Flask-Migrate |
| Frontend | React 18 (CRA), Axios, react-dropzone, react-markdown |
| Styling | Vanilla CSS, Google Fonts (Syne + DM Sans + DM Mono) |

---

## Features

- 🗂️ **Multi-session** — create, rename, and delete independent Q&A sessions
- 📄 **Drag-and-drop PDF upload** with real-time processing progress
- 🤖 **RAG-powered answers** — LangChain retrieves the top-6 relevant chunks; tinyroberta-squad2 generates grounded extractive responses
- 📎 **Source citations** — every assistant reply shows clickable source cards with filename, page number, and snippet
- 💬 **Conversation memory** — multi-turn chat history used as context
- 🛢️ **MySQL persistence** — sessions, documents, and full chat history survive restarts
- 🎨 **Premium dark UI** with glassmorphism, micro-animations, and typography
- 🔒 **No OpenAI / no API key needed** — all models run locally

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8 running locally (or via Docker)
- ~2 GB disk space for HuggingFace model cache (auto-downloaded on first run)

---

## Setup & Run

### 1. Clone & configure the backend

```bash
cd backend

# Create .env from example
copy .env.example .env
```

Edit `.env` and fill in:
```
DB_PASSWORD=your-mysql-password
```

### 2. Create the MySQL database

```sql
-- In MySQL shell or Workbench:
CREATE DATABASE ai_doc_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

> First run will download `all-MiniLM-L6-v2` and `tinyroberta-squad2` from HuggingFace (~500 MB total). Subsequent runs use the local cache.

### 4. Initialize the database tables

```bash
python init_db.py
# Output: ✅ Database tables created successfully.
```

### 5. Start the backend

```bash
python run.py
# Flask running on http://127.0.0.1:5000
```

### 6. Install & start the frontend

```bash
cd frontend
npm install
npm start
# CRA dev server on http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (DB + embeddings status) |
| `GET` | `/api/sessions/` | List all sessions |
| `POST` | `/api/sessions/` | Create session `{"name": "..."}` |
| `GET` | `/api/sessions/<id>` | Get session with messages + docs |
| `PATCH` | `/api/sessions/<id>` | Rename session |
| `DELETE` | `/api/sessions/<id>` | Delete session + all files (cascade) |
| `DELETE` | `/api/sessions/<id>/clear` | Clear chat history |
| `POST` | `/api/documents/upload/<session_id>` | Upload PDF (multipart/form-data) |
| `GET` | `/api/documents/session/<session_id>` | List docs for session |
| `DELETE` | `/api/documents/<doc_id>` | Delete document + vector store |
| `POST` | `/api/chat/ask/<session_id>` | Ask a question `{"question": "..."}` |

---

## Project Structure

```
ai-doc-qa/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── models/__init__.py   # Session, Document, Message models
│   │   ├── routes/
│   │   │   ├── sessions.py      # Session CRUD + file cleanup on delete
│   │   │   ├── documents.py     # PDF upload & async processing
│   │   │   ├── chat.py          # RAG Q&A endpoint
│   │   │   └── health.py        # Health check (DB + embeddings)
│   │   └── services/
│   │       └── rag_service.py   # LangChain RAG pipeline (local models)
│   ├── requirements.txt
│   ├── run.py
│   └── init_db.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx    # Chat UI with markdown + citations
│   │   │   ├── Sidebar.jsx      # Session management
│   │   │   ├── DropZone.jsx     # Drag-and-drop upload
│   │   │   └── RightPanel.jsx   # Stats + pipeline info
│   │   ├── hooks/useSession.js  # React data hooks
│   │   ├── services/api.js      # Axios API client
│   │   ├── styles/global.css    # Design system + CSS variables
│   │   └── App.jsx
│   └── package.json
└── docker-compose.yml
```

---

## RAG Pipeline

```
PDF Upload
   ↓
PyPDFLoader → page extraction
   ↓
RecursiveCharacterTextSplitter (500 chars, 80 overlap)
   ↓
all-MiniLM-L6-v2 → local vector embeddings
   ↓
FAISS local vector store (persisted to disk)
   ↓
On question: similarity search → top-6 chunks retrieved
   ↓
Query type detection (summary / list / factual / contact / count)
   ↓
tinyroberta-squad2 (extractive QA) → answer + confidence score
   ↓
Answer + source citations → stored in MySQL + returned to UI
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `ai_doc_qa` | Database name |
| `DB_USER` | `root` | MySQL user |
| `DB_PASSWORD` | — | **Required.** MySQL password |
| `UPLOAD_FOLDER` | `uploads` | PDF storage directory |
| `VECTOR_STORE_PATH` | `vector_stores` | FAISS index directory |
| `FRONTEND_URL` | `http://localhost:3000` | CORS allowed origin |
| `MAX_CONTENT_LENGTH` | `52428800` | Max upload size (50 MB) |
| `SECRET_KEY` | `dev-secret-key` | Flask session secret |