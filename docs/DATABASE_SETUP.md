# PostgreSQL and migrations

Local database defaults are in `docker-compose.yml`. Start it with `docker compose up -d postgres`. The backend uses SQLAlchemy 2.0 and psycopg 3.

```bash
cd backend
alembic upgrade head
python -m app.seed
```

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

Never use development `create_all` as a production migration strategy. Back up the database before production migrations.
