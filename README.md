# Korean Vocab

V0.1 full-stack starter: Next.js frontend, FastAPI backend, and PostgreSQL for local development.

## Prerequisites

- Node.js 20.9 or newer
- Python 3.11 or newer
- Docker Desktop with Docker Compose

## Start PostgreSQL

From the repository root, copy `.env.example` to `.env`, then run:

```powershell
docker compose up -d db
```

The database listens on `localhost:5433` (host port 5432 is already in use on this machine). The credentials in `.env.example` are for local development only.

## Start the API

In PowerShell:

```powershell
cd backend
Copy-Item .env.example .env
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; interactive API docs are at `http://localhost:8000/docs`.
The database readiness endpoint is `http://localhost:8000/health/database`.

Authentication endpoints are `/auth/register`, `/auth/login`, `/auth/logout`, and `/auth/me`. Registration creates the account and sets the HttpOnly auth cookie. For production, set `SECRET_KEY` to a unique random secret of at least 32 characters and set `AUTH_COOKIE_SECURE=true`; configure `CORS_ORIGINS` with the exact frontend origins.

Vocabulary endpoints are `GET /categories` and authenticated `GET`, `POST`, `PUT`, and `DELETE /vocabularies` routes. The list endpoint supports server-side `search`, `category_id`, `level`, `sort`, `page`, and `limit` query parameters.

The dashboard endpoint is `GET /dashboard/stats` and returns total words, counts by level, categories in use, and counts by category for the signed-in user.

Run backend tests from `backend/` with `pytest`.

## Start the frontend

In a separate terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm run dev
```

The frontend is available at `http://localhost:3000`.
The browser calls the API at `NEXT_PUBLIC_API_URL` with credentials enabled. For local development, the client automatically matches `localhost` or `127.0.0.1` between the frontend and API so the `SameSite=Lax` authentication cookie stays same-site. Keep the frontend origin in the backend `CORS_ORIGINS` allowlist.

The root URL redirects to `/dashboard`. Main routes are `/login`, `/register`, `/dashboard`, `/vocabulary`, `/vocabulary/new`, `/vocabulary/[id]`, and `/vocabulary/[id]/edit`.

## Current foundation

- `frontend/`: Next.js App Router with TypeScript and Tailwind CSS; separate auth, dashboard, list, create, detail, and edit routes.
- `backend/`: FastAPI health endpoints, environment-based settings, SQLAlchemy models, Alembic migrations, and tests.
- `compose.yaml`: PostgreSQL service with a persistent named volume and health check.

The initial database migration creates `users`, `categories`, and `vocabularies`; a follow-up migration seeds the six predefined categories. Authentication, dashboard statistics, and user-scoped vocabulary management are implemented in the API.