# RideCare Roadmap

What has shipped on `main`, and what comes next. Product overview: [README.md](README.md).

Honest scope: RideCare is a **well-engineered personal garage** (data → calculation → display), not yet an intelligent vehicle platform. Redis, cursor pagination, and indexes are real design choices; they are **not** a claim of proven 10k-user load. The roadmap below is ordered by **what a rider needs next**, not by internal engineering phases.

---

## Shipped

### Auth & security
- Register / login with JWT access tokens (httpOnly cookies)
- **Email verification** — magic link on register (Brevo HTTPS on Render free; SMTP locally); login blocked until confirmed; resend endpoint
- **Forgot / reset password** — magic link; one-shot Redis token; resets password and revokes all sessions
- Changing email resets verification, sends a new link, and clears sessions
- Refresh-token rotation in Redis; logout revokes sessions
- Password strength policy; profile + password change with session revoke **and cookie clear**
- **Delete account** — password-confirmed; cascades garage data and cleans storage
- Access-token blocklisting in Redis (`jti`) on logout / refresh; per-user revoke epoch on password change
- IP- and user-based rate limiting (user limiter pipelined with auth Redis reads)
- Foreign / missing resources return **404** (anti-enumeration), not 403

### Vehicles & odometer
- Multi-vehicle CRUD with ownership checks
- Live odometer = `max(baseline, fuel max, service max)`
- Cursor-paginated vehicle list + garage **Load more**
- Baseline change recalculates stored fuel mileage
- `GET /vehicles/{id}/summary` — spend, mileage, recent fill-ups, next service, **service_reminder**, **document_reminders**
- `GET /vehicles/{id}/analytics` — totals, **cost-per-km (fuel + service)**, last-10 mileage trend, last-6 months fuel spend
- `GET /vehicles/compare` — side-by-side spend, mileage, and ₹/km across the garage

### Fuel & mileage
- Fill-up logging with server-side liters and km/L
- Timeline-aware odometer validation
- Full mileage recalculation on create / update / delete / baseline change
- Stable cursor pagination (date + id) + fuel tab **Load more**
- **CSV export** of full fuel history (`GET /fuel_logs/export`)
- **CSV import** of fuel history (`POST /fuel_logs/import`) — export-compatible; all-or-nothing validation + one mileage recalc

### Service history
- Service visits with tags, cost, and next-due fields
- `GET /service_logs/next` for reminders
- **Suggest next-due** from the maintenance catalog (`POST /service_logs/suggest-next-due` + “Fill from guide” in the form)
- Cursor-paginated list + service tab **Load more**
- Partial PATCH validates next-service odometer against existing reading
- Reminder clears once a visit meets the due date or odometer
- **CSV export** of full service history (`GET /service_logs/export`)
- **CSV import** of service history (`POST /service_logs/import`) — export-compatible; all-or-nothing validation

### Documents
- Insurance / licence / RC vault via Supabase Storage
- Typed uploads (PDF / JPEG / PNG, 10 MB), signed download URLs
- Clear expiry date / notes on update
- Vehicle delete removes linked storage objects
- Document writes invalidate vehicle summary cache (reminder freshness)
- Cursor-paginated list + docs tab **Load more**; API returns `days_until` / `expiry_status`

### Reminders & email digests
- **In-app reminders** on the dashboard — service soon/overdue + document expiry
- **Daily email digests** via GitHub Actions → `POST /internal/reminder-digests` (midnight IST)
- Per-user toggles: service due emails / document expiry emails (Settings)

### Maintenance guide
- Static JSON catalog (24 tasks) with in-memory cache
- Filterable API + `/maintenance` page (component / severity)
- Catalog-driven due suggestions only — not usage-based prediction

### Caching & platform
- Redis cache for vehicle list/detail, summary, analytics, and compare
- Write-through invalidation on fuel / service / vehicle / document writes
- Auth hot path: one Redis pipeline for rate limit + blocklist + revoke-epoch + user identity; warm requests skip the Postgres user lookup
- Identity cache invalidated on profile / password change
- Query-shaped **composite indexes** (`vehicle_id`/`owner_id` + sort columns) for list/pagination paths
- Alembic migrations, async SQLAlchemy, GitHub Actions CI (**backend pytest**)
- Deployed API (Render) + frontend (Vercel) with same-origin `/api` proxy for cookies
- Local Vite `/api` proxy to `127.0.0.1:8000` (same-origin cookies, no Windows `localhost` IPv6 delay)

### Frontend product surface
- Dark rider UI: auth (login · register · **check-email** · **verify-email** · **forgot-password** · **reset-password**), garage, compare, vehicle detail (Fuel · Service · Docs · Analytics)
- Dashboard driven by the summary API
- Settings: profile, password, email reminder toggles, delete account
- Error boundary, 404 page
- Recharts analytics: cost-per-km, summary cards, mileage trend, monthly fuel spend (descriptive, not predictive)

---

## Evolution (rider journey)

```
Today:     log → see mileage / reminders / charts
Next:      bring history in → quiet idle bikes → get told what to do
Later:     less typing (OCR), family garage, shops, live telemetry
```

Frontend stays intentionally thin; testing investment stays on API / domain correctness (backend pytest). No Playwright / frontend CI required for this portfolio track.

Refactor fat routes (`vehicles.py`, `auth.py`) toward services/repositories **only when the next feature forces a change** — no premature layer soup.

---

## Next

Ordered by how a real rider feels the product. Hardening Phases 1–2 already shipped on `main` (concurrency tests, request IDs, Dependabot).

### Done — Bring my history in (CSV import)

Fuel + service CSV import ships on this branch: same columns as export, row-level errors, all-or-nothing write, Import CSV on the Fuel / Service tabs. liters/mileage ignored and recalculated server-side.

### 1 — Keep the bike, stop the nagging (per-vehicle mute)

**Rider pain:** “This Pulsar is parked / sold / seasonal. I want the records, not insurance and service emails every week.” Account-level Settings toggles kill reminders for *every* bike.

- Per-vehicle mute (keep data, quiet reminders)
- Dashboard in-app reminders skip muted bikes
- Daily digest emails skip muted bikes
- Obvious toggle on vehicle edit/detail (“Reminders off — history kept”)

**Done when:** a multi-bike rider can silence idle machines and still open them for history, export, and compare.

### 2 — Tell me what to do next (RideCare Health)

**Rider pain:** “I already logged the data — now what? When is service actually due? Is mileage getting worse?” Static catalog tips are not enough once history exists (especially after import).

- Usage-based **maintenance prediction** (last service + riding rate + catalog interval → due in X km / around date Y)
- Mileage **anomaly / decline** with a plain-language recommendation
- Analytics **confidence** (“₹/km from N fill-ups over K km”) so empty or thin data does not look authoritative
- Optional simple **health** summary on the vehicle — signals from the API, not a chatbot

**Done when:** on one real bike with history, the rider sees a predicted next service and at least one actionable signal they did not have to calculate themselves.

---

## Under the hood (only as needed)

Riders do not ask for these; ship them when import/Health make them necessary — not as a blocking “phase” before product value.

- Incremental mileage recalc and SQL aggregates for summary/analytics (large imports + Health reads)
- Sync Supabase storage off the event loop; cheap DB `CHECK`s on odometer/cost/price
- Light before/after timings only for changes you actually ship (no fake 100k-user campaign)

Defer unless felt: magic-byte upload hardening, signed-URL list redesign, Redis namespace versioning, cached pagination `total`, async account-delete storage cleanup, Sentry.

---

## Later

### Still for the rider (after mute + Health)

- Stronger warnings when odometer timelines look wrong
- Richer insurance fields (policy / insurer) on top of expiry reminders
- Push notifications (email digests already ship)
- **OCR** — photo of RC / insurance / invoice → confirm → auto-fill (less typing than CSV for some riders)

### Platform / ecosystem (not the near-term product bet)

- Multi-rider / household / fleet **RBAC**
- Mechanic / service-center marketplace
- Real telemetry (OBD / Bluetooth / auto odometer)
- Job queue for email, OCR, exports, cleanup
- Disaster-recovery runbook; deeper vendor abstraction (Supabase / Upstash / Render / Brevo)
