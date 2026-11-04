# Aashiyana full-stack setup

## Prerequisites
- Node.js 20.11+ and npm
- Docker Desktop / Docker Engine with Compose
- Python 3.11+ (3.12 recommended)

## 1. Configure the frontend

```bash
cp .env.example .env.local
npm install
```

For local full-stack development set:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_USE_API=true
NEXT_PUBLIC_DEV_AUTH_EMAIL=developer@aashiyana.local
NEXT_PUBLIC_FIREBASE_PROJECT_ID=aashiyana
```

The dev email header is only accepted when the backend has `DEV_AUTH_BYPASS=true`. It is a local-only convenience, not authentication. Never enable it on a public or production deployment. For real auth, leave `NEXT_PUBLIC_DEV_AUTH_EMAIL` empty and configure Firebase.

## 2. Start PostgreSQL and API

```bash
docker compose up --build -d postgres api
docker compose logs -f api
```

The development API creates missing tables on startup. For a migration-managed database, use Alembic:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

If using Docker Compose, seed from the backend container:

```bash
docker compose exec api python -m app.seed
```

API docs: http://localhost:8000/docs
Health: http://localhost:8000/api/health

## 3. Start Next.js

In a second terminal:

```bash
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_USE_API=true` to use PostgreSQL-backed search, property detail, favourites, enquiries, visits, listing submission and dashboard endpoints. Set it to `false` for the original localStorage-only showcase.

## 4. Local admin access

For the local dev bypass, sign in to the frontend using the same email as `NEXT_PUBLIC_DEV_AUTH_EMAIL`. Then grant admin in the backend database:

```bash
cd backend
DEV_AUTH_BYPASS=true python -m scripts.promote_admin developer@aashiyana.local
```

The script requires the account to exist. Visiting the dashboard while signed in creates the development user record. With the Docker Compose API, run `docker compose exec api python -m scripts.promote_admin developer@aashiyana.local`. To revoke:

```bash
python -m scripts.revoke_admin developer@aashiyana.local
```

For production, provision an admin through a trusted database/admin process; there is deliberately no public admin registration endpoint.

## 5. Tests

```bash
cd backend
python -m pytest -q
```

Frontend typecheck/build:

```bash
npm run lint
npm run build
```

## 6. Production checklist
- `ENVIRONMENT=production`, `DEV_AUTH_BYPASS=false`
- Managed PostgreSQL and `alembic upgrade head`
- Firebase Authentication enabled for Google and Phone providers
- Backend Firebase Admin service account secret configured
- Exact production frontend origins in `CORS_ORIGINS`
- Cloudinary credentials configured before enabling image uploads
- Google Maps JavaScript API and Places API enabled, domain-restricted browser key configured
- HTTPS, backups, monitoring, error reporting, rate limiting/WAF and email provider configured
- Review privacy notice, terms, consent language, retention policy, DPDP obligations and real estate/RERA legal requirements with qualified counsel
- Replace demo seed content/images with licensed, verified inventory; demo properties are marked `demo=true`
- Set `NEXT_PUBLIC_USE_API=true`, `NEXT_PUBLIC_DEV_AUTH_EMAIL` empty

No RERA number or verification state is validated by this application. `rera_verified` defaults false and must only be set by a documented verification process.
