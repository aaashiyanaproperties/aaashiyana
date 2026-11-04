# Aashiyana REST API

Base path: `/api`. Interactive OpenAPI documentation is exposed at `/docs`, with the raw schema at `/openapi.json` and ReDoc at `/redoc`.

Open `http://localhost:8000/docs` when running the local Docker Compose stack, or open `<backend HTTPS URL>/docs` after deploying the API. In Swagger UI, use **Authorize** and enter a Firebase ID token (without the `Bearer ` prefix) to test protected endpoints. The local Compose stack enables the development-only auth bypass; for those requests, use the `X-Dev-User` header field instead. Do not enable that bypass in production.

## Public
- `GET /health`
- `GET /properties` — query: `q`, `city`, `locality`, `transaction_type`, `property_type`, `min_price`, `max_price`, `bedrooms`, `bathrooms`, `furnishing`, `possession_status`, `pincode`, `verified`, `featured`, `parking`, `amenity`, `min_area`, `max_area`, `posted_within_days`, `sort`, `page`, `page_size`
- `GET /properties/{slug}`
- `GET /locations?q=`
- `GET /projects?city=`
- `GET /agents`, `GET /developers`, `GET /blog`
- `POST /properties/{id}/inquiries`, `POST /properties/{id}/visits`, `POST /properties/{id}/reports`
- `POST /contact-messages`, `POST /newsletter`, `GET /categories`

## Authenticated (Firebase bearer token)
- `GET/PATCH /me`
- `GET /me/properties`, `GET /me/favourites`, `POST/DELETE /properties/{id}/favourite`
- `POST /properties`, `POST /properties/drafts`, `PATCH/DELETE /properties/{id}` (owner or admin)
- `GET /me/inquiries`, `PATCH /inquiries/{id}`, `GET /me/visits`
- `GET/POST /me/saved-searches`, `GET /me/notifications`, `PATCH /me/notifications/{id}`
- `POST /uploads` (Cloudinary configured)

## Admin role required
- `GET /admin/overview`, `/admin/properties`, `/admin/users`, `/admin/reports`, `/admin/audit-logs`, `/admin/projects`
- `POST /admin/properties/{id}/moderate`, `DELETE /admin/properties/{id}`
- `PATCH /admin/users/{id}/roles`, `PATCH /admin/reports/{id}`
- `POST /admin/projects`, `/admin/developers`, `/admin/agents`, `/admin/blog`, `/admin/categories`, `/admin/locations`
- `GET /admin/contact-messages`, `/admin/settings`; `PUT /admin/settings/{key}`; `PATCH /admin/properties/{id}/feature`

Authentication and role checks are performed on the backend. Public inquiry/visit requests do not reveal owner email/phone. In-app notification rows are persisted. Optional SMTP email delivery is attempted for owner enquiry/visit alerts and contact-form messages when SMTP and `CONTACT_EMAIL` are configured; SMS is not integrated. Newsletter sign-ups are stored but no campaign delivery is sent. Payment, paid promotion, RERA verification, full Google Places autocomplete and transactional messaging require separate provider/product decisions and are not implemented as live integrations.
