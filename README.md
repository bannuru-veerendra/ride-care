# RideCare

RideCare is a personal vehicle companion app designed to make ownership simple, organized, and stress-free.

It supports bike, car, and other personal vehicle owners.

## Vision

RideCare helps vehicle owners track maintenance, fuel spending, and important documents in one place.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI |
| Database | PostgreSQL (Supabase) |
| File Storage | Supabase Storage |
| Cache | Redis (Upstash) |
| Frontend | React 19, TypeScript, Vite |
| UI | Tailwind CSS v4, shadcn/ui |
| Client state | TanStack Query, Zustand, Axios |

## Project Structure

```
RideCare/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── utils/
│   ├── migrations/
│   ├── tests/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   │   ├── ui/          # shadcn components
│   │   │   └── common/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── vehicles/
│   │   │   ├── fuel-logs/
│   │   │   ├── service-logs/
│   │   │   └── documents/   # hooks live under each feature
│   │   ├── lib/             # axios, query-client, utils
│   │   ├── pages/
│   │   ├── store/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── .env.example
│   └── .env.production
├── .github/workflows/
├── .gitignore
├── README.md
└── ROADMAP.md
```

## Getting Started (Backend)

### Prerequisites

- Python 3.10+
- A Supabase project (PostgreSQL + Storage)
- An Upstash Redis instance (optional for now)

### Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then fill in your values
```

### Run

```bash
uvicorn main:app --reload
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Test

Tests use a separate Supabase project via `backend/.env.test` (never commit this file).

1. Copy secrets into `backend/.env.test` (test DB URL, JWT, Supabase, Redis).
2. Apply migrations to the test database once:

```bash
cp .env .env.backup
cp .env.test .env
alembic upgrade head
cp .env.backup .env
```

3. Run the suite (`tests/conftest.py` sets `ENV_FILE=.env.test` so pytest never hits your dev DB):

```bash
pytest tests/ -v
```

All backend API tests should pass (auth, vehicles, fuel logs, service logs, documents).
GitHub Actions CI runs the same suite using repository secrets.

### Swagger authentication

- **Register / login (JSON):** use `POST /auth/register` and `POST /auth/login` with `email` + `password`.
- **Authorize button in Swagger:** uses `POST /auth/token` (form body). Set **username** to your email and **password** to your password.

## Getting Started (Frontend)

### Prerequisites

- Node.js 20+
- Backend running at `http://localhost:8000` (or update `VITE_API_URL`)

### Setup

```bash
cd frontend
npm install
cp .env.example .env
# For local: set VITE_API_URL=http://localhost:8000 in frontend/.env
```

`.env.example` and `.env.production` default to a Render placeholder (`https://your-backend.onrender.com`). Replace that with your live backend URL before deploying. Vite uses `.env` for `npm run dev` and `.env.production` for `npm run build`.

### Run

```bash
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

### Other scripts

```bash
npm run build    # tsc -b && vite build
npm run lint     # oxlint
npm run preview  # preview production build
```

`frontend/public/_redirects` enables SPA routing on Vercel so deep links (for example `/vehicles/:id`) refresh correctly.

## API Overview

| Module | Endpoints | Notes |
|--------|-----------|-------|
| Auth | `/auth/register`, `/auth/login`, `/auth/token` | JWT bearer auth |
| Vehicles | `/vehicles/` CRUD | `baseline_odometer` at registration (legacy `current_odometer` still accepted); response `current_odometer` is live (max of baseline, fuel, service) |
| Fuel logs | `/fuel_logs/` CRUD | Auto-calculates km/L; validates odometer against baseline or previous fill-up |
| Service logs | `/service_logs/` CRUD, `/service_logs/next` | Tracks services and next service date/odometer |
| Documents | `/documents/` CRUD | Multipart upload (PDF/JPEG/PNG); types: insurance, driving license, RC; signed download URLs |

All vehicle-scoped routes require `?vehicle_id=<uuid>` and a valid `Authorization: Bearer <token>` header.

Document create/update use `multipart/form-data` in Swagger (same pattern as file upload forms).

## Status

| Area | Status |
|------|--------|
| Backend scaffolding | Done |
| Database & config | Done |
| Auth (register, login, JWT) | Done |
| Vehicles CRUD | Done |
| Fuel logs (mileage, validation) | Done |
| Service logs (history, next service) | Done |
| Document vault (upload, metadata, signed URLs) | Done |
| Document API tests | Done |
| Frontend scaffolding | Done |
| Frontend auth (login, register, protected routes) | Done |
| Frontend vehicles (list, create, edit, delete, detail) | Done |
| Frontend fuel logs (entry, history on vehicle detail) | Done |
| Frontend service logs (entry, history on vehicle detail) | Done |
| Frontend documents vault (upload, edit, signed URLs) | Done |
| Dashboard (stats, next-service reminder) | Done |
| Error boundary + 404 page | Done |
| Deployment prep (env, SPA redirects, CI secrets) | Done |

See [ROADMAP.md](ROADMAP.md) for planned features.

## Environment Variables

| File | Purpose | Commit? |
|------|---------|---------|
| `backend/.env` | Local/dev Database, Supabase, Redis, JWT | No |
| `backend/.env.test` | Test DB and secrets for pytest | No |
| `backend/.env.example` | Placeholder names for backend setup | Yes |
| `frontend/.env` | Local `VITE_API_URL` (usually `http://localhost:8000`) | No |
| `frontend/.env.example` | Documented production API URL template | Yes |
| `frontend/.env.production` | Production `VITE_API_URL` used by `vite build` | Yes (no secrets) |

Copy each `.env.example` to `.env` (and create `.env.test` for the test project). Never commit secret-bearing env files — they are listed in `.gitignore`.
