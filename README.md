# Claudinary — AI-Powered Image Asset Management Platform

Production-ready, AI-driven visual asset management platform with automated scene tagging, subject-aware smart cropping, on-demand background removal, and an admin moderation queue.

---

## 1. Architecture & Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.x (Async), Pydantic v2, Alembic, PostgreSQL, Redis.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, React Router, Lucide Icons.
- **Media Engine**: Cloudinary (Smart cropping `g_auto`, delivery optimization `f_auto, q_auto`, AI background removal, auto-tagging).
- **Target Deployment**:
  - Frontend: Vercel
  - Backend: Render
  - Database: Neon PostgreSQL
  - Cache: Upstash Redis
  - Storage/CDN: Cloudinary

---

## 2. Directory Structure

```
claudinary/
├── backend/
│   ├── app/
│   │   ├── api/             # API v1 routes (health, assets, search, admin, webhooks)
│   │   ├── core/            # Config, security, rate limiting, logging
│   │   ├── db/              # SQLAlchemy 2 models & repositories
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/        # Business logic, Cloudinary, Moderation/Vision abstractions
│   │   └── workers/         # Background tasks
│   ├── alembic/             # Database migrations
│   ├── tests/               # Unit and integration test suite
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Backend container
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── layouts/         # Root layout with navbar & health status
│   │   ├── pages/           # Gallery, Upload, AssetDetail, Moderation, Stats
│   │   ├── services/        # Axios API wrapper
│   │   └── types/           # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── .gitignore
├── .dockerignore
├── .env.example
└── README.md
```

---

## 3. Quick Start & Setup Instructions

### Step 1: Clone and Configure Environment

Copy `.env.example` to `.env` in the root (or `backend/.env` and `frontend/.env`):

```bash
cp .env.example .env
```

### Step 2: Backend Virtual Environment & Dependencies

Create and activate a Python 3.12 virtual environment:

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Run Database & Cache (Docker Compose)

Start PostgreSQL and Redis:
```bash
docker compose up postgres redis -d
```

### Step 4: Run Database Migrations

Apply Alembic migrations to set up tables (`assets`, `asset_tags`, `processing_states`) and indexes:
```bash
cd backend
alembic upgrade head
```

### Step 5: Start Backend Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/api/v1/health`

### Step 6: Frontend Setup & Development

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be live at: `http://localhost:5173`

---

## 4. Running Tests

Run the test suite inside the `backend` folder with your virtual environment activated:

```bash
cd backend
pytest
```

---

## 5. Security & Protection

- **Admin Routes**: Protected via `X-Admin-API-Key` header (`ADMIN_API_KEY`).
- **File Validation**: MIME type and file header / magic bytes are validated on raw buffers before storage.
- **Upload Rate Limiting**: 20 uploads/minute per client via Redis sliding window (with automatic in-memory fallback).
- **Public Visibility**: Assets in `PENDING` or `REJECTED` status are isolated from the public catalog.
