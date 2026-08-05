# RideCare Product Roadmap

Living checklist of what shipped and what’s next. For a product + architecture overview, see [README.md](README.md).

Status is aligned with GitHub `main` (merged through **PR #39**) plus in-progress work on `feature/analytics-charts`.

---

## Completed (Backend) — on `main`

### Auth & users
- Registration and login with JWT access tokens
- Refresh-token rotation stored in Redis; logout revokes refresh sessions (**PR #30**)
- Password strength policy (bcrypt hashing)
- `GET/PATCH /users/me` and `PATCH /users/me/password` (**PR #32**)
- Rate limiting on auth and general API traffic (**PR #31**)

### Vehicles
- Full CRUD with ownership checks
- Baseline odometer at registration (legacy `current_odometer` accepted)
- Live odometer = max(baseline, fuel max, service max)
- Cursor-paginated list (`CursorPage`: items, next_cursor, has_more, total) (**PR #33**)
- `GET /vehicles/{id}/summary` — all-log spend/mileage aggregates, recent fill-ups, next service (**PR #35 / #36**)

### Fuel and mileage
- Log fill-ups (date, odometer, cost, price per liter, notes)
- Server-side liters and km/L calculation
- Odometer validated against baseline or previous fill-up (timeline-aware)
- Full mileage recalculation on create / update / delete
- Baseline never overwritten by fuel logs
- Cursor-paginated list (newest first) (**PR #33**)

### Service history
- Log visits (center, cost, services done, next date / odometer, notes)
- `GET /service_logs/next` for dashboard reminders
- Next service derived from the most recent visit; optional fields clearable (**PR #34**)
- Cursor-paginated list (newest first)

### Document vault
- Upload to Supabase Storage (PDF, JPEG, PNG; max 10 MB)
- Types: insurance, driving license, registration certificate
- Metadata (expiry, notes); replace file or update fields
- Signed download URLs; DB and storage stay consistent on delete

### Maintenance guidelines (**PR #38**)
- Static catalog in `backend/data/maintenance_guidelines.json` (24 tasks)
- Loader with `lru_cache` (`app/data/guidelines.py`)
- `GET /maintenance-guidelines/` with severity + component filters
- `GET …/components` and `GET …/severity-levels` for UI dropdowns
- Auth required; no DB / Redis needed for the catalog itself

### Caching (**PR #37**)
- Redis caching utility (`app/utils/cache.py`) with non-fatal get/set/delete helpers
- Vehicle list cached per user (cursor/size in key); vehicle detail cached per ID
- Next-service endpoint cached per vehicle
- Write-through invalidation on create/update/delete
- Pattern-based invalidation via `SCAN`
- Ownership verified on cache hit for detail endpoints
- TTLs: 5 min for vehicles and next-service

### Platform & quality
- Shared cursor pagination utility (`app/utils/pagination.py`)
- Alembic migrations; async SQLAlchemy + PostgreSQL
- Automated API tests: auth, users, vehicles, fuel, service, documents, pagination, caching, summary, guidelines
- Isolated test project via `backend/.env.test` + `ENV_FILE`
- GitHub Actions CI; Render/Vercel deployment config (**PR #25–#29**)

---

## Completed (Frontend) — on `main`

### Scaffolding
- Vite + React 19 + TypeScript
- Tailwind CSS v4 and shadcn/ui
- Feature folders: auth, vehicles, fuel-logs, service-logs, documents, users, maintenance
- Axios JWT client, TanStack Query, Zustand auth store
- App shell: router, layout, navbar, account menu

### Auth & settings
- Login / register + protected routes
- Logout with refresh cleanup
- Settings: profile update and password change (**PR #32**)

### Garage & vehicle detail
- Vehicle list, create, edit, delete
- Detail tabs: Fuel · Service · Docs
- Thin client over `CursorPage` (`items` / `total`)

### Fuel, service, documents
- Sheet-based create / edit flows
- Fuel cards centered on km/L; service cards with tags and next-due
- Document cards with expiry cues and signed-URL open

### Dashboard (**PR #36**)
- Multi-bike picker, odometer, avg mileage, next-service countdown
- Monthly spend + mileage trend from **summary API** (not client-side aggregation over one page)
- Quick actions deep-linking into fuel / service tabs

### Maintenance (**PR #39**)
- `/maintenance` page: guidelines grouped by component
- Severity / component filters (sheet + active pills)
- Expandable guideline cards

### Resilience & deploy
- Error boundary + 404 page
- Production `VITE_API_URL`, `tsc -b && vite build`, Vercel SPA `_redirects`
- Secrets kept out of git via root `.gitignore`

---

## In progress — `feature/analytics-charts` (not yet on `main`)

### Backend
- `GET /vehicles/{id}/analytics` — totals, best/worst/avg mileage, last-10 trend, last-6 monthly spend (SQL over all fuel logs)
- Redis cache for **summary** and **analytics** (5 min TTL) with invalidation on fuel/service/vehicle writes
- Dedicated analytics + extended cache tests

### Frontend
- Vehicle detail **Analytics** tab (Recharts): summary cards, mileage trend, monthly spend, insight callout
- `useVehicleAnalytics` + fuel-log mutation invalidation
- Fuel tab **Load more** via `useInfiniteFuelLogs` (cursor pages)

---

## Planned

### Insurance management
- Structured policy fields (provider, number, coverage) beyond the vault file
- Expiry reminders and renewal tracking

### Maintenance (next step)
- Odometer / last-service–driven due dates on top of the static guidelines catalog
- Optional vehicle-type filtering (chain vs CVT, liquid-cooled vs air-cooled)

### Notifications
- Upcoming service and document-expiry reminders (email / push — TBD)
- Prefer server-side scheduling; Redis already in stack for auth, rate limits, and response cache

### List UX
- Load more / infinite scroll for **service** lists (fuel Load more is in the analytics branch)
- Keep pagination logic on the API; frontend stays a consumer

### Documents API
- Cursor pagination for document lists (parity with vehicles / fuel / service)

### Dashboard / analytics polish
- Wire dashboard fully off summary only (drop any leftover first-page fuel fetches where still used)
- Optional Redis TTL tuning / cache metrics

---

## Future scope

- Export (CSV / PDF) for fill-ups and service history
- Multi-rider / shared garage permissions
- AI assists: fuel-price context, natural-language “when is my next service?” answers
- Deeper cost analytics (per-km fuel + service over longer ranges, comparisons across bikes)
