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

## Completed (Frontend)

### Scaffolding
- Vite + React 19 + TypeScript project setup
- Tailwind CSS v4 and shadcn/ui configuration
- Feature-based folder structure (`auth`, `vehicles`, `fuel-logs`, `service-logs`, `documents`)
- Axios client with JWT interceptors (`src/lib/axios.ts`)
- React Query client (`src/lib/query-client.ts`)
- Zustand auth store with persistence (`src/store/auth.store.ts`)
- App shell with `BrowserRouter`, `QueryClientProvider`, layout, and navbar

### Auth & core UI
- Login and register pages
- Protected routes
- shadcn/ui components (`Button`, `Input`, `Sheet`, `Tabs`, `Toaster`, etc.)
- `src/lib/utils.ts` (`cn` helper)

### Vehicles
- Vehicle list, create, edit, and delete
- Vehicle detail page with tabbed fuel / service / documents sections

### Fuel logs
- Log fill-ups from the vehicle detail Fuel tab
- Fuel history cards with mileage as the primary metric
- Create, edit, and delete via Sheet + React Query hooks

### Service logs
- Log service visits from the vehicle detail Service tab
- Service history cards (cost, services done, next service hints)
- Common service badges plus custom service entry
- Create, edit, and delete via Sheet + React Query hooks
- API client and `useNextService` hook ready (`GET /service_logs/next`)

### Documents
- Upload and manage documents from the vehicle detail Docs tab
- Document cards with expiry warnings and signed-URL viewing
- Create, edit (metadata / replace file), and delete via Sheet + React Query hooks

### Dashboard
- Home hub with vehicle picker, fuel spend / mileage stats, and quick actions
- Next-service reminder from `GET /service_logs/next` (overdue and soon-within-14-days)
- Deep links into vehicle fuel / service tabs

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
