# RideCare Roadmap

What has shipped on `main`, and what comes next. Product overview: [README.md](README.md).

Honest scope: RideCare is a **well-engineered personal garage** (data → calculation → display), not yet an intelligent vehicle platform. Redis, cursor pagination, and indexes are real design choices; they are **not** a claim of proven 10k-user load. Next work hardens what exists, then adds one genuinely proactive product slice.

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

### Service history
- Service visits with tags, cost, and next-due fields
- `GET /service_logs/next` for reminders
- **Suggest next-due** from the maintenance catalog (`POST /service_logs/suggest-next-due` + “Fill from guide” in the form)
- Cursor-paginated list + service tab **Load more**
- Partial PATCH validates next-service odometer against existing reading
- Reminder clears once a visit meets the due date or odometer
- **CSV export** of full service history (`GET /service_logs/export`)

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

## Evolution

```
v1 (now):  record → calculate → remind → display
v2 (next product): understand behavior → predict → recommend action
```

Frontend stays intentionally thin; testing investment stays on API / domain correctness (backend pytest). No Playwright / frontend CI required for this portfolio track.

Refactor fat routes (`vehicles.py`, `auth.py`) toward services/repositories **only when the next feature forces a change** — no premature layer soup.

---

## Next

Harden the existing system before adding more product surface. Order matters.

### Intended concurrency guarantees

| Area | Guarantee |
|------|-----------|
| **Refresh rotation** | Same refresh token used twice → **exactly one** successful rotation; the other request fails |
| **Fuel logging** | Concurrent creates on one vehicle → correct mileage, no lost updates, consistent timeline order |
| **Account delete** | DB transaction commits first; storage cleanup is **async / enqueued** after commit |

### Phase 1 — Correctness

- Concurrent refresh-token rotation races (same token → one win / one reject) — covered in `tests/test_concurrency.py`
- Concurrent fuel creates on the same vehicle — covered
- Cache stampede + invalidation races — covered
- Transaction / rollback boundaries across Postgres + Redis (failed fuel create leaves warm summary cache) — covered
- Idempotency / duplicate side-effects for reminder digests (concurrent cron → at most one email via Redis NX) — covered

**Done when:** those concurrency + rollback + stampede tests exist and CI (pytest) is green; retry-sensitive ops have an explicit duplicate-side-effect note or fix.

### Phase 2 — Production hardening

- Error tracking (e.g. Sentry) — deferred (not shipping a third-party error SaaS for now)
- Structured logs + request IDs — `X-Request-ID` middleware + `ridecare.access` lines (`method/path/status/duration_ms/request_id`)
- API / DB latency and error-rate visibility — per-request `duration_ms`; WARN on slow (≥1s) or 4xx; ERROR on 5xx / unhandled
- Dependabot / secret scanning / dependency audit — `.github/dependabot.yml` + non-blocking `pip-audit` in CI; enable GitHub **Secret scanning** + **Push protection** in repo settings
- Soften README toward problem → solution → demo → architecture → trade-offs (engineering evidence below the fold)

**Done when:** request IDs + structured logs ship; basic API latency visibility exists; dependency/secret scanning is enabled. (External error SaaS optional later.)

### Phase 3 — Performance & data-access cleanup

- Summary / analytics: SQL aggregates (`SUM` / `AVG` / `COUNT` / `GROUP BY`) instead of loading full histories into Python
- Mileage recalc from the **affected row onward**
- Sync Supabase storage SDK off the event loop (thread pool or async client)
- Document uploads: stream + size while reading; **magic-byte** checks; signed URLs **on demand** (or short cache) — no list N+1
- Account delete: **enqueue orphan storage cleanup** after DB commit (short request path)
- DB `CHECK` constraints (`odometer > 0`, `total_cost > 0`, `price_per_liter > 0`)
- Pagination: optional or cached `total`; cursor + `has_more` as the hot path
- Prefer versioned Redis namespaces over `SCAN` pattern deletes when key counts grow

**Done when:** analytics/summary use SQL aggregates; storage does not block the event loop; mileage is incremental; signed URL list N+1 is gone; DB CHECKs land; account delete cleanup is async.

### Phase 4 — Measure (prove, don’t claim)

Benchmark a representative dataset first (do **not** invent target numbers). Example shape: ~100k fuel / ~20k service / ~10k vehicles — size to what the test DB can hold.

Record for `summary`, `analytics`, `compare`, fuel list, service list:

- p50 / p95 / p99
- DB time
- Redis hit / miss rate (especially summary + analytics)

Publish before → after for Phase 3 changes (e.g. analytics P95 after SQL aggregates + cache).

**Done when:** a short benchmark note exists with before/after timings and Redis hit rates — evidence of design, not slogans.

### Phase 5 — First intelligent product slice: RideCare Health

Flagship evolution — uses data already in the system (fuel, service, odometer, catalog, dates). Not a chatbot bolted on.

- Usage-based **maintenance prediction** (last service + rate + catalog interval → due in X km / expected date)
- Mileage **anomaly / decline** signals with actionable recommendations
- Analytics **confidence / data coverage** (e.g. ₹/km based on N fuel + M service over K km)
- Optional vehicle **health score** UI fed by structured API signals

**Done when:** one vehicle can show predicted next service + at least one anomaly/recommendation from real history (not static JSON alone).

---

## Later

After Health / prediction is real. Platform and ecosystem — not the immediate portfolio bet.

- **OCR** for RC / insurance / service invoices → confirm → auto-fill logs
- Push notifications (email digests already ship)
- Stronger data-quality / reconciliation for suspicious odometer timelines
- Multi-rider / household / fleet **RBAC**
- Mechanic / service-center marketplace (due → nearby shop → appointment → invoice → history)
- Real telemetry (OBD / Bluetooth / auto odometer)
- Structured insurance fields; general job queue for email, OCR, exports, cleanup
- Disaster-recovery runbook; deeper vendor abstraction (Supabase / Upstash / Render / Brevo)
