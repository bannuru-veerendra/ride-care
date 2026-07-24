# RideCare Product Roadmap

Living checklist of what shipped and what’s next. For a product + architecture overview, see [README.md](README.md).

---

## Completed (Backend)

### Auth & users
- Registration and login with JWT access tokens
- Refresh-token rotation stored in Redis; logout revokes refresh sessions
- Password strength policy (bcrypt hashing)
- `GET/PATCH /users/me` and `PATCH /users/me/password`
- Rate limiting on auth and general API traffic

### Vehicles
- Full CRUD with ownership checks
- Baseline odometer at registration (legacy `current_odometer` accepted)
- Live odometer = max(baseline, fuel max, service max)
- Cursor-paginated list (`CursorPage`: items, next_cursor, has_more, total)

### Fuel and mileage
- Log fill-ups (date, odometer, cost, price per liter, notes)
- Server-side liters and km/L calculation
- Odometer validated against baseline or previous fill-up (timeline-aware)
- Full mileage recalculation on create / update / delete
- Baseline never overwritten by fuel logs
- Cursor-paginated list (newest first)

### Service history
- Log visits (center, cost, services done, next date / odometer, notes)
- `GET /service_logs/next` for dashboard reminders
- Cursor-paginated list (newest first)

### Document vault
- Upload to Supabase Storage (PDF, JPEG, PNG; max 10 MB)
- Types: insurance, driving license, registration certificate
- Metadata (expiry, notes); replace file or update fields
- Signed download URLs; DB and storage stay consistent on delete

### Platform & quality
- Shared cursor pagination utility (`app/utils/pagination.py`)
- Alembic migrations; async SQLAlchemy + PostgreSQL
- Automated API tests: auth, users, vehicles, fuel, service, documents, pagination
- Isolated test project via `backend/.env.test` + `ENV_FILE`
- GitHub Actions CI with repository secrets

---

## Completed (Frontend)

### Scaffolding
- Vite + React 19 + TypeScript
- Tailwind CSS v4 and shadcn/ui
- Feature folders: auth, vehicles, fuel-logs, service-logs, documents, users
- Axios JWT client, TanStack Query, Zustand auth store
- App shell: router, layout, navbar, account menu

### Auth & settings
- Login / register + protected routes
- Logout with refresh cleanup
- Settings: profile update and password change

### Garage & vehicle detail
- Vehicle list, create, edit, delete
- Detail tabs: Fuel · Service · Docs
- Thin client over `CursorPage` (`items` / `total`)

### Fuel, service, documents
- Sheet-based create / edit flows
- Fuel cards centered on km/L; service cards with tags and next-due
- Document cards with expiry cues and signed-URL open

### Dashboard
- Multi-bike picker, odometer, avg mileage, next-service countdown
- Monthly spend + mileage trend
- Quick actions deep-linking into fuel / service tabs

### Resilience & deploy
- Error boundary + 404 page
- Production `VITE_API_URL`, `tsc -b && vite build`, Vercel SPA `_redirects`
- Secrets kept out of git via root `.gitignore`

---

## Planned

### Insurance management
- Structured policy fields (provider, number, coverage) beyond the vault file
- Expiry reminders and renewal tracking

### Maintenance guidance
- Interval suggestions (oil, chain, filters) driven by odometer and last service

### Notifications
- Upcoming service and document-expiry reminders (email / push — TBD)
- Prefer server-side scheduling; Redis already in stack for auth and rate limits

### List UX (optional)
- Infinite scroll or “load more” on fuel / service when totals exceed the default page
- Keep pagination logic on the API; frontend stays a consumer

### Documents API
- Cursor pagination for document lists (parity with vehicles / fuel / service)

---

## Future scope

- Cost analytics (per-km fuel + service over time)
- Export (CSV / PDF) for fill-ups and service history
- Multi-rider / shared garage permissions
- AI assists: fuel-price context, natural-language “when is my next service?” answers
