# TraderCopilot (Sale-Ready)

Web-first trading signals + advisor. Designed to be deployable in minutes (Railway + Vercel), with clear demo flows and minimal operational burden.

## What you can demo in 2–3 minutes
See DEMO.md.

## Core features
- LITE / PRO signal generation
- Logs & history per token/mode (if enabled)
- Evaluation flow (if enabled)
- Clean API (FastAPI) + web UI (Vite/React)
- Sale-ready repository hygiene (no secrets in git)

## Local run (quick)
### Backend
1) Create venv, install deps
2) Configure env vars (see .env.example)
3) Run uvicorn

### Web
1) Configure VITE_API_BASE_URL
2) npm ci && npm run dev

## Environment variables
- Backend: see backend/.env.example (no real secrets)
- Web: VITE_API_BASE_URL

## Deploy
- Backend: Railway (root backend/, uvicorn start)
- Web: Vercel (root web/, VITE_API_BASE_URL pointing to Railway)
