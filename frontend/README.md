# Frontend

This directory contains the initial React interface for the post-consultation API.

## Local development

Start the FastAPI backend from the repo root:

```powershell
uvicorn src.api.main:app --reload
```

Then install frontend dependencies and start Vite:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/analyze` and `/health` to `http://127.0.0.1:8000`.
