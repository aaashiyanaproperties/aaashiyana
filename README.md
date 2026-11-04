# Aashiyana — Full-stack Indian Real Estate Marketplace

Aashiyana is a full-stack marketplace codebase built around the existing Aashiyana frontend. It combines a responsive Next.js App Router application with a FastAPI REST API and PostgreSQL persistence.

## What is included

### Frontend
- Responsive homepage, buy, rent, commercial, projects, agents, builders, property details, blog, contact, about, help, privacy, cookie, terms and careers pages.
- Search against the API with location/locality/PIN-code discovery, price, property type, bedrooms, bathrooms, furnishing, possession, parking, amenity, area, RERA flag, posted date, sort and pagination filters.
- Grid/list/map-split result views. Google Maps renders markers when the key and property coordinates are configured; otherwise the UI explains what is missing.
- Firebase Google sign-in and phone OTP/reCAPTCHA integration, with a clearly labelled local demo sign-in when Firebase web credentials are absent.
- Favourites, saved searches, profile, dashboard, seller listing wizard, persistent drafts, edit/resubmit, enquiry and visit workflows.
- Admin moderation, role assignment, reports, contact message review and platform summary views.
- Local browser demo mode remains available by setting `NEXT_PUBLIC_USE_API=false`.

### Backend
- FastAPI endpoints with Pydantic validation and SQLAlchemy 2 models.
- PostgreSQL relational schema and Alembic migration.
- Firebase Admin ID-token verification and backend role checks.
- Property search/detail/create/draft/edit/soft-delete, image upload, favourites, saved searches, inquiries, visit requests/statuses, notifications, reports and moderation.
- Developer/project/agent/category/location/blog administration, user roles, audit logs, platform settings, contact messages and newsletter subscriptions.
- Optional Cloudinary uploads and SMTP email notifications. Provider credentials are never fabricated.
- Seed script creates 36 clearly marked demo properties plus locations, amenities, projects, agents, developers and one editorial entry.

## Run locally

1. Copy `.env.example` to `.env.local`.
2. Start PostgreSQL and the API: `docker compose up --build -d postgres api`.
3. Seed demo data: `docker compose exec api python -m app.seed`.
4. Install and run the frontend: `npm install && npm run dev`.
5. Open http://localhost:3000. API docs: http://localhost:8000/docs.

The local compose stack intentionally enables a development-only identity bypass. Never deploy that setting. Full instructions are in `docs/SETUP.md`.

## Verification performed in this build environment
- Backend Python compile check: passed.
- Backend API tests: **7 passed** using SQLite test storage.
- Alembic initial migration: applied successfully against SQLite as a migration smoke test.
- Seed smoke test: 36 demo property records and related sample entities created; public API endpoints returned successfully.
- TypeScript/JSX syntax scan: no syntax diagnostics.
- Full Next.js dependency installation and production build were **not verified** because npm dependency installation timed out in this environment. Run `npm install`, `npm run lint` and `npm run build` locally after downloading dependencies.

## Important production gaps
- Configure Firebase, PostgreSQL, Cloudinary, Google Maps and SMTP with real credentials.
- Google Places API autocomplete, SMS, payments, paid promotions, RERA registry verification, automated legal document checks and full external CRM integrations are not included as live services.
- SMTP notifications are optional; newsletter addresses are stored but no campaign delivery is sent.
- The admin API is role-protected, but the deployment operator must provision the first admin through a trusted process.
- Legal pages are draft copy and require Indian legal review, including DPDP and real-estate/RERA obligations.
- Demo seed records and sample imagery are not real listings, verified agents, reviews or marketplace activity.

## Documentation
- `docs/SETUP.md`
- `docs/FIREBASE_SETUP.md`
- `docs/GOOGLE_MAPS_SETUP.md`
- `docs/DATABASE_SETUP.md`
- `docs/DEPLOYMENT.md`
- `docs/API_DOCUMENTATION.md`
