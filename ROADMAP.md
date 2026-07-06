# RideCare Product Roadmap

## Completed (Backend)

### Auth & vehicles
- User registration and login (JWT)
- Vehicle CRUD with baseline odometer at registration

### Fuel and mileage tracking
- Log fill-ups (date, odometer, cost, price per liter)
- Auto-calculate liters and km/L (mileage)
- Validate odometer against vehicle baseline (first entry) or previous fill-up
- Recalculate mileage on update, including later fill-ups when date/odometer changes
- Vehicle baseline odometer is not overwritten by fuel logs

### Service history
- Log service visits (center, cost, services performed, notes)
- Track next service date and odometer
- `GET /service_logs/next` returns the upcoming scheduled service

### Document vault
- Upload vehicle documents to Supabase Storage (PDF, JPEG, PNG; max 10 MB)
- Document types: insurance, driving license, registration certificate
- Link documents to vehicles with optional expiry date and notes
- List, get, update metadata, replace file, and delete via `/documents/` API
- Signed URLs for secure file access
- DB and storage kept consistent on create, update, and delete

### Quality
- Automated API tests for auth, vehicles, fuel logs, service logs, and documents

---

## Completed (Frontend — scaffolding)

- Vite + React 19 + TypeScript project setup
- Tailwind CSS v4 and shadcn/ui configuration
- Feature-based folder structure (`auth`, `vehicles`, `fuel-logs`, `service-logs`, `documents`)
- Axios client with JWT interceptors (`src/lib/axios.ts`)
- React Query client (`src/lib/query-client.ts`)
- Zustand auth store with persistence (`src/store/auth.store.ts`)
- App shell with `BrowserRouter` and `QueryClientProvider`

---

## In Progress

### Frontend — auth & core UI
- Login and register pages
- Protected routes
- shadcn/ui components (`Button`, `Input`, `Toaster`, etc.)
- `src/lib/utils.ts` (`cn` helper)

### Frontend — feature screens
- Vehicle list and detail
- Fuel log entry and history
- Service log entry and next-service view
- Document upload and vault

---

## Planned

### Insurance management
- Policy details beyond file storage (provider, policy number, coverage)
- Expiry reminders and renewal tracking

### Maintenance guidance
- Practical maintenance recommendations (for example, oil change intervals and chain lubrication timing)

### Notifications
- Reminders for upcoming service and insurance expiry (Redis / push — TBD)

---

## Future Scope

- AI-powered enhancements, such as live fuel price insights and personalized responses to rider questions
