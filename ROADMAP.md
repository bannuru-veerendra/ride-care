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
- 57 automated API tests (auth, vehicles, fuel logs, service logs)

---

## In Progress

### Document API tests
- Automated tests for document upload, update, and delete (mocked Supabase storage)

---

## Planned

### Insurance management
- Policy details beyond file storage (provider, policy number, coverage)
- Expiry reminders and renewal tracking

### Maintenance guidance
- Practical maintenance recommendations (for example, oil change intervals and chain lubrication timing)

### Frontend
- React app for riders to manage vehicles, fuel, services, and documents

### Notifications
- Reminders for upcoming service and insurance expiry (Redis / push — TBD)

---

## Future Scope

- AI-powered enhancements, such as live fuel price insights and personalized responses to rider questions
