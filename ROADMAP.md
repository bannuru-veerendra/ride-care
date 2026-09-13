# RideCare Roadmap

What has shipped on `main`, and what comes next. Product overview: [README.md](README.md).

Honest scope: RideCare is a **well-engineered personal garage** (data → calculation → display), not yet an intelligent vehicle platform. The long-term product bet is **digital vehicle health and ownership history** — not “another expense tracker.” Redis, cursor pagination, and indexes are real design choices; they are **not** a claim of proven 10k-user load. The roadmap below is ordered by **what a rider needs next**, not by pitch-deck phases.

**Constraint that stays true for every Health / prediction feature:** only ship signals the current data can support (fuel, service tags + due fields, documents, odometer). Thin history must show confidence or a fallback — never a fake score or authoritative-looking guess.

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
- **Per-vehicle mute** — quiet dashboard + digest reminders; history / export / compare stay available
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
Today:     personal garage — log → mileage / reminders / charts
Next:      vehicle health layer — predict → recommend → one clear next action
Then:      less typing (OCR) → denser history → annual report / cost forecast
Later:     shops write history → verified records → resale passport → commerce
```

Positioning over time: **personal garage → health layer → ownership history → service connections.** Marketplace and bookings only after riders keep a persistent history.

Frontend stays intentionally thin; testing investment stays on API / domain correctness (backend pytest). No Playwright / frontend CI required for this portfolio track.

Refactor fat routes (`vehicles.py`, `auth.py`) toward services/repositories **only when the next feature forces a change** — no premature layer soup.

---

## Next

Ordered by how a real rider feels the product. Hardening Phases 1–2 already shipped on `main` (concurrency tests, request IDs, Dependabot).

### Done — Bring my history in (CSV import)

Fuel + service CSV import ships on `main`: same columns as export, row-level errors, all-or-nothing write, Import CSV on the Fuel / Service tabs. liters/mileage ignored and recalculated server-side.

### Done — Keep the bike, stop the nagging (per-vehicle mute)

`reminders_muted` on each vehicle. Summary API returns empty reminder signals when muted; daily digests skip muted bikes. Toggle on vehicle edit + detail (“Reminders off — history kept”).

### 1 — Documents vault that fits real Indian bikes

**Rider pain:** “I have more than three papers, Pollution is due soon, and the vault only shows a useless upload filename.” Today the Docs tab is a fixed Insurance / Licence / RC trio — no Pollution, no custom types, no document identity fields, and the original filename sticks around after upload.

- **Many docs per vehicle** — stop treating the vault as “one slot per enum”; owner can upload multiple certificates (e.g. two insurance policies over time, Pollution + RC + DL).
- **Type picker:** dropdown for the four common certificates — **RC, DL, Insurance, Pollution** — plus a free-text name when it is something else (Aadhaar, Form 20, hypothecation letter, …).
- **Expiry only when it matters:** show / require expiry for **DL, Insurance, Pollution**; **RC has no expiry field** (omit from UI and reminder digests).
- **Drop original filename** — do not store or display the upload’s file name after save; it adds noise and is not rider data.
- **Certificate identity on the card** — store and show type-relevant details instead of the filename (e.g. DL number for driving licence, policy / insurer for insurance, PUC number for Pollution, registration number already known for RC). Custom-named docs get a short label / ID field the rider fills in.

**Done when:** a multi-bike rider can keep Pollution + DL + Insurance with the right expiry behaviour, add a one-off custom paper, and open Docs to see certificate details — not `scan_final_v2.pdf`.

### 2 — Tell me what to do next (RideCare Health)

**Rider pain:** “I already logged the data — now what? When is service actually due? Is mileage getting worse?” Static catalog tips are not enough once history exists (especially after import).

**Ship as ranked, evidence-backed signals + one recommended action** — not a cosmetic “Health Score: 82/100” and not component rows the data cannot justify (pad wear, chain slack, tyre age). Start from what already exists: document expiry, next-service date/km, catalog interval vs last matching service tag, riding rate from odometer history, mileage trend when sample size is enough.

- Usage-based **maintenance prediction** (last service + riding rate + catalog / rider interval → due in X km / around date Y). Show the inputs. Thin history falls back honestly (“not enough riding data — using the date you set”).
- Dashboard / home framed as **“what should I do today?”** — one next action above quick stats, not another chart wall.
- Mileage **anomaly / decline** with a plain-language recommendation when N fill-ups is enough
- Analytics **confidence** (“₹/km from N fill-ups over K km”) so empty or thin data does not look authoritative
- Optional **health summary** on the vehicle — signals from the API, not a chatbot

**Done when:** on one real bike with history, the rider sees a predicted next service and at least one actionable signal they did not have to calculate themselves.

### 3 — Vehicle timeline (everything that happened)

**Rider pain:** fuel, service, and docs live on separate tabs; the bike’s story is hard to read as one history.

- Single chronological feed on the vehicle: fuel, service, and document events (date, cost / liters / tags, odometer where relevant)
- Reuse existing log APIs — no new domain model required for v1

**Done when:** a rider can scroll one list and answer “what happened to this bike?” without switching tabs.

### 4 — Smarter digests (same pipes, better copy)

Daily digests already ship. Once prediction exists, upgrade copy from countdown-only (“Service soon · 1 day · 636 km”) to usage-aware language (“likely within 1–2 weeks at your recent riding”) with the same service / document signals. Keep per-user toggles and muted vehicles as-is. Document digests follow the new vault rules (no RC expiry nags; Pollution / DL / Insurance still remind).

**Done when:** the email states a predicted window (or an honest fallback) instead of only a static countdown.

---

## Validate before the big bets

Engineering is ahead of demand proof. Before OCR, shop products, or paid “passport” features, put real riders on the live app and watch:

- register → add vehicle → import or log fuel/service → return at 7 / 30 days
- open reminder emails → act on a reminder
- “Would you be disappointed if RideCare disappeared tomorrow?”

Optional early monetization signal (not a build blocker for Health): a small Pro price for predictions, reports, OCR, advanced reminders — even a handful of paying riders beats another unshipped chart. Do **not** wait for 10k users to learn whether anyone will pay.

---

## Under the hood (only as needed)

Riders do not ask for these; ship them when import/Health make them necessary — not as a blocking “phase” before product value.

- Incremental mileage recalc and SQL aggregates for summary/analytics (large imports + Health reads)
- Sync Supabase storage off the event loop; cheap DB `CHECK`s on odometer/cost/price
- Light before/after timings only for changes you actually ship (no fake 100k-user campaign)

Defer unless felt: magic-byte upload hardening, signed-URL list redesign, Redis namespace versioning, cached pagination `total`, async account-delete storage cleanup, Sentry.

---

## After Health (still for the rider)

Ship these only when Health is live and riders feel the friction — not as a parallel rewrite.

### Less typing

- **OCR** — photo of RC / insurance / invoice → structured draft → **user confirms** → backend validates → save (never AI write-through)
- Optional invoice / receipt attach on service even before OCR
- WhatsApp / email receipt forwarding only if riders ask for it

### Richer service record (optional fields, not a heavier form)

Today: date, odometer, tags, total cost, next due, notes, optional service center. Next generation may add **optional** labour / parts line items, invoice attachment, photos — without making line items required to log a visit. Default path stays fast; structured history grows when riders choose it.

### Vehicle intelligence (needs dense history)

- Running-cost **forecast** (ranges + sample size; never a single false-precision number)
- Cost / fuel-efficiency anomaly when the bike’s own history supports it
- Annual / on-demand **vehicle health report** (ownership span, km, spend, ₹/km, service + document status) — valuable for resale later; embarrassing with two fill-ups, so gate on data density
- “Is this bike getting expensive?” vs **that bike’s** prior year first; cross-user “typical model ₹/km” only with a real fleet

### Still useful polish

- Stronger warnings when odometer timelines look wrong
- Push notifications (email digests already ship)

---

## Later (platform / ecosystem — not the near-term bet)

Correct sequence: riders keep history → shops want to write into that history → transactions. Do **not** build a mechanic marketplace first.

- Service-center pilot: shop accounts, customer invite, job complete → owner history update, customer approval
- **Verified vs self-reported** service entries (only after a real second party writes data)
- RideCare **Vehicle Passport** / resale report as a product someone might pay for
- Commerce only after the data loop works: discover → book → service → record → predict
- Multi-rider / household / fleet **RBAC**
- Real telemetry (OBD / Bluetooth / auto odometer)
- Job queue for email, OCR, exports, cleanup
- Disaster-recovery runbook; deeper vendor abstraction (Supabase / Upstash / Render / Brevo)

---

## Explicitly not next

Do not prioritize: more charts for their own sake, a generic AI chatbot, social / community, crypto, native apps before web retention, microservices / Kubernetes / event architecture theater, or marketplace before rider validation. The bottleneck is customer value, retention, and distribution — not more platform sophistication.
