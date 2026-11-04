# Deployment outline

## Frontend (Vercel)
- Import the repository and set Root Directory to the project root (or the frontend root if split during deployment).
- Build command: `npm run build`; output is managed by Next.js.
- Configure `NEXT_PUBLIC_API_URL` to the HTTPS API URL, `NEXT_PUBLIC_USE_API=true`, Firebase web config and the restricted Google Maps browser key.
- Leave `NEXT_PUBLIC_DEV_AUTH_EMAIL` empty.

## Backend
- Deploy `backend/` as a Python 3.12 service; install `backend/requirements.txt`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (set working directory to `backend`).
- The interactive Swagger UI is available at `<backend HTTPS URL>/docs`; the OpenAPI schema is at `/openapi.json`. Use **Authorize** in Swagger UI with a Firebase ID token to test authenticated endpoints.
- Configure `DATABASE_URL`, `ENVIRONMENT=production`, `DEV_AUTH_BYPASS=false`, `CORS_ORIGINS`, Firebase Admin JSON and Cloudinary secrets and optional SMTP/CONTACT_EMAIL settings.
- Run `alembic upgrade head` as a release/pre-deploy command. Run seed only for a new development/staging database.

## Database
Use a managed PostgreSQL 15+ service with automated backups, SSL, connection limits and restricted network access. Supply the provider's SQLAlchemy psycopg URL as `DATABASE_URL`.

This repository provides a production-oriented foundation, not a claim of completed security review, legal review, operational monitoring or third-party provisioning. Complete the checklist in `SETUP.md` before accepting real users or payments.
