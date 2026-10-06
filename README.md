# Duolingo Web-App Clone — Phase 0

A fullstack Duolingo web-app clone built with Next.js App Router, FastAPI, SQLAlchemy 2, Pydantic v2, and SQLite.

## 1. Monorepo Organization

```
DuoLingoClone/
├── frontend/             # Next.js App Router, TypeScript, Tailwind, Zustand, TanStack Query
├── backend/              # Python 3.12+, FastAPI, SQLAlchemy 2, Pydantic v2, SQLite
├── docs/                 # Specifications and system architecture
│   ├── SCHEMA.md         # Database schema (13 tables, cascades, check constraints)
│   ├── API.md            # REST API contract and endpoint specifications
│   ├── DESIGN.md         # Design system tokens, state machine, and Framer Motion patterns
│   └── ARCHITECTURE.md   # System flow, authoritative attempt model, logical clock
├── data/                 # Local SQLite database directory (runtime created, gitignored)
│   └── duolingo_clone.db
├── .gitignore            # Git ignore rules for Python, Node, data/*.db
└── README.md             # Developer getting started and verification guide
```

---

## 2. Technology Stack

- **Frontend**: Next.js App Router + TypeScript + Tailwind CSS + Zustand + TanStack React Query + Framer Motion + Nunito Font.
- **Backend**: Python 3.12+ + FastAPI + SQLAlchemy 2 + Pydantic v2 + SQLite locally.
- **API Typing**: `openapi-typescript` generates frontend types directly from backend `/openapi.json`.
- **API Access**: Proxied via Next.js `/api/*` rewrites to `BACKEND_URL` (default `http://127.0.0.1:8000`).
- **Identity**: Authoritative default user ID `1` supplied via `X-User-Id` header (no passwords/JWT).
- **Database**: Local SQLite stored at `./data/duolingo_clone.db`, enforced with `PRAGMA foreign_keys = ON;`.

---

## 3. Getting Started

### 3.1 Prerequisites
- Python 3.12+ (or 3.13)
- Node.js 18+ (tested on Node v22)
- npm 10+

### 3.2 Backend Setup & Execution

1. Navigate to the backend directory and activate the virtual environment:
   ```bash
   cd backend
   # Windows PowerShell:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```
2. Install dependencies (if setting up fresh):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Run backend tests and linting:
   ```bash
   pytest tests -v
   ruff check .
   ```
5. Export current OpenAPI specification:
   ```bash
   python export_openapi.py
   ```

### 3.3 Frontend Setup & Execution

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Generate TypeScript API types from OpenAPI:
   ```bash
   npm run generate:api
   ```
   *(Or if the backend server is running live: `npm run generate:api:remote`)*
4. Run the frontend development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.
5. Run frontend lint and type-checking:
   ```bash
   npm run lint
   npm run typecheck
   ```

---

## 4. Environment Variables

### Backend (`backend/.env`)
| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/duolingo_clone.db` | SQLAlchemy SQLite connection string |
| `ENABLE_DEBUG` | `true` | Enables `/api/debug/*` endpoints for user 1 |
| `BACKEND_HOST` | `0.0.0.0` | Host interface for uvicorn |
| `BACKEND_PORT` | `8000` | Port for uvicorn |

### Frontend (`frontend/.env.local`)
| Variable | Default | Description |
|---|---|---|
| `BACKEND_URL` | `http://127.0.0.1:8000` | Target FastAPI backend URL for `/api/*` rewrites |

---

## 5. Phase-0 Gate Verification Checklist

- [x] `docs/SCHEMA.md`, `docs/API.md`, `docs/DESIGN.md`, and `docs/ARCHITECTURE.md` exist and match locked specification.
- [x] `backend/` and `frontend/` are independently runnable.
- [x] Backend health endpoints (`GET /health` and `GET /api/health`) return 200 with DB status.
- [x] SQLite connection enforces `PRAGMA foreign_keys = ON;`.
- [x] Local DB path is `./data/duolingo_clone.db` and `./data` is automatically created.
- [x] Next.js `/api/*` proxy rewrite dynamically targets `BACKEND_URL`.
- [x] `openapi-typescript` generates strict types from `/openapi.json`.
- [x] Phase-0 fixture API routes supply representative responses for all locked contracts.
- [x] No premature Phase-1 business logic or data seeding implemented.
- [x] Passes all type checks, linters, and test suites.
