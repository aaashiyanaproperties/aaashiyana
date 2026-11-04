# Backend integration roadmap

## API contract proposal

- `GET /api/properties` — query: `purpose`, `city`, `locality`, `type`, `price_min`, `price_max`, `beds`, `sort`, `page`, `page_size`
- `GET /api/properties/{slug}` — public property detail
- `POST /api/properties` — authenticated listing draft creation
- `PATCH /api/properties/{id}` — owner/agent listing update
- `POST /api/properties/{id}/submit` — submit listing for moderation
- `POST /api/inquiries` — create enquiry
- `GET /api/me/inquiries` — current user's sent enquiries
- `GET /api/owner/inquiries` — enquiries received by current owner/agent
- `POST /api/properties/{id}/visits` — request a visit
- `GET/POST/DELETE /api/me/favourites` — manage favourites
- `GET /api/me/listings` — current user's listings
- `GET /api/admin/listings?status=pending` — admin moderation queue
- `POST /api/admin/listings/{id}/approve` — admin approval
- `POST /api/admin/listings/{id}/reject` — admin rejection with reason

## Frontend service boundary

Create typed service modules under `services/` for `properties`, `auth`, `favourites`, `inquiries`, `visits`, `uploads` and `admin`. Each module should use a shared fetch client that adds Firebase ID tokens, normalizes API errors, handles 401/403 responses and applies request timeouts. Keep demo adapters separate from production adapters.

## Security gates before production

- Verify Firebase ID tokens server-side.
- Resolve roles from trusted backend records, never from client-submitted role fields.
- Enforce ownership checks on every listing, enquiry and media mutation.
- Make admin role assignment invitation/operations-only; no public admin registration.
- Validate image MIME type, file signature, file size and image dimensions server-side.
- Add request rate limits for OTP, contact, inquiry, report and upload endpoints.
- Keep contact details private unless a listing owner explicitly opts into display.
- Add audit events for moderation, role changes and listing status changes.
