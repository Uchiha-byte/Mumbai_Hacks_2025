# TruthScan Frontend

Next.js frontend for TruthScan, including:
- Home dashboard
- Quick Check view (fast analysis)
- Analyze view (deep analysis)

## Prerequisites

- Node.js 18+
- npm 9+
- Backend running on `http://localhost:8000`

## Local Development

```bash
npm install
npm run dev
```

Frontend starts at: `http://localhost:3000`

## Backend Dependency

This app calls the FastAPI backend (`/api/v1/analyze`, `/api/v1/quick-analyze`, etc.).  
If backend is not running, analysis views will fail.

Start backend from project root:

```bash
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Build

```bash
npm run build
npm run start
```

## Notes

- Keep API keys only in backend `.env` (never in frontend env files).
- For best stability, run backend from the project virtualenv (`backend/.venv`).
