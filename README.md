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
| Frontend | React (planned) |

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
│   ├── alembic.ini
│   ├── tests/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/          (planned)
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

# Deactivate (Windows, macOS, and Linux)
deactivate
```

### Run

```bash
uvicorn main:app --reload
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Status

| Area | Status |
|------|--------|
| Backend scaffolding | Done |
| Database & config | Done |
| API routes & models | In progress (auth, vehicles, fuel logs) |
| Frontend | Not started |

See [ROADMAP.md](ROADMAP.md) for planned features.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your credentials.

Never commit `.env` — it is listed in `.gitignore`.
