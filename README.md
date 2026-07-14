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
│   │   │   └── documents/
│   │   ├── hooks/
│   │   ├── lib/             # axios, query-client, utils
│   │   ├── pages/
│   │   ├── store/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── .env.example
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

```bash
pytest tests/ -v
```

All backend API tests should pass (auth, vehicles, fuel logs, service logs, documents).

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
cp .env.example .env   # VITE_API_URL=http://localhost:8000
```

### Run

```bash
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

### Other scripts

```bash
npm run build    # production build
npm run lint     # oxlint
npm run preview  # preview production build
```

## API Overview

| Module | Endpoints | Notes |
|--------|-----------|-------|
| Auth | `/auth/register`, `/auth/login`, `/auth/token` | JWT bearer auth |
| Vehicles | `/vehicles/` CRUD | `current_odometer` is a fixed baseline at registration |
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
| Frontend vehicles (list, create, detail) | Done |
| Frontend fuel logs (entry, history on vehicle detail) | Done |
| Frontend service logs (entry, history on vehicle detail) | Done |
| Frontend documents vault (upload, edit, signed URLs) | Done |
| Next-service reminder UI | Planned |

See [ROADMAP.md](ROADMAP.md) for planned features.

## Environment Variables

| File | Purpose |
|------|---------|
| `backend/.env` | Database, Supabase, Redis, JWT secrets |
| `frontend/.env` | `VITE_API_URL` — backend base URL for Axios |

Copy each `.env.example` to `.env` and fill in your values. Never commit `.env` files — they are listed in `.gitignore`.
