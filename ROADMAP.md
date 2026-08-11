# RideCare Roadmap

What has shipped on `main`, and what comes next. Product overview: [README.md](README.md).

---

## Shipped

### Auth & security
- Register / login with JWT access tokens (httpOnly cookies)
- Refresh-token rotation in Redis; logout revokes sessions
- Password strength policy; profile + password change with session revoke **and cookie clear**
- Access-token blocklisting in Redis (`jti`) on logout / refresh; per-user revoke epoch on password change
- IP- and user-based rate limiting

### Vehicles & odometer
- Multi-vehicle CRUD with ownership checks
- Live odometer = `max(baseline, fuel max, service max)`
- Cursor-paginated vehicle list + garage **Load more**
- Baseline change recalculates stored fuel mileage
- `GET /vehicles/{id}/summary` — spend, mileage, recent fill-ups, next service, **service_reminder**, **document_reminders**
- `GET /vehicles/{id}/analytics` — totals, trend series, monthly spend (SQL over all logs)

### Fuel & mileage
- Fill-up logging with server-side liters and km/L
- Timeline-aware odometer validation
- Full mileage recalculation on create / update / delete / baseline change
- Stable cursor pagination (date + id) + fuel tab **Load more**

### Service history
- Service visits with tags, cost, and next-due fields
- `GET /service_logs/next` for reminders (cached nulls are real hits)
- Cursor-paginated list + service tab **Load more**
- Partial PATCH validates next-service odometer against existing reading

### Documents
- Insurance / licence / RC vault via Supabase Storage
- Typed uploads (PDF / JPEG / PNG, 10 MB), signed download URLs
- Clear expiry date / notes on update
- Vehicle delete removes linked storage objects
- Document writes invalidate vehicle summary cache (reminder freshness)

### Maintenance guide
- Static JSON catalog (24 tasks) with in-memory cache
- Filterable API + `/maintenance` page (component / severity)

### Caching & platform
- Redis cache for vehicle list/detail, summary, analytics, and next-service
- Write-through invalidation on fuel / service / vehicle / document writes
- Alembic migrations, async SQLAlchemy, GitHub Actions CI
- Deployed API (Render) + frontend (Vercel) with same-origin `/api` proxy for cookies

### Frontend product surface
- Dark rider UI: auth, garage, vehicle detail (Fuel · Service · Docs · Analytics)
- Dashboard driven by the summary API
- **In-app reminders** on the dashboard — service soon/overdue + document expiry (no email/push yet)
- Settings (profile / password), error boundary, 404 page
- Recharts analytics: summary cards, mileage trend, monthly spend

---

## Next

### Reminders beyond the app
- Email / push for service-due and document-expiry
- Prefer server-side scheduling; Redis is already in the stack

### Smarter maintenance
- Due dates driven by odometer / last service on top of the static catalog
- Optional vehicle-type filters (chain vs CVT, liquid- vs air-cooled)

### Insurance beyond the vault
- Structured policy fields (provider, number, coverage)
- Expiry and renewal tracking

### List & export polish
- Load more for documents lists
- Cursor pagination for documents API
- CSV / PDF export for fill-ups and service history

### Deeper analytics
- Longer-range cost-per-km (fuel + service)
- Cross-bike comparisons

---

## Later

- Multi-rider / shared garage permissions
- AI assists: natural-language “when is my next service?”, fuel-price context
