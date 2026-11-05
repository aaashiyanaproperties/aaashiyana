# Backend data-access architecture

The backend follows a layered request path:

```text
FastAPI endpoint -> service -> domain DAO -> NamedParameterJdbcTemplate -> datasource -> database
```

- `backend/app/api/endpoints/` contains resource-specific HTTP routers. `backend/app/api/routes.py` only composes those routers.
- `backend/app/services/` owns business rules, authorization-adjacent checks, and transaction orchestration.
- `backend/app/dao/repositories.py` exposes domain DAO classes. DAOs use named SQL statement keys rather than constructing SQL.
- `backend/app/dao/template.py` implements named-parameter queries using SQLAlchemy Core `Connection` and `text()`. It does not use ORM sessions or ORM queries.
- `backend/app/dao/sql.properties` is the source for application SQL. Add and reference a named key for each query; values can use Java-properties continuation lines ending in `\`.
- `backend/app/db/datasource.py` configures the connection pool from `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `DB_POOL_RECYCLE_SECONDS`. The FastAPI connection dependency opens one transaction per request and commits on success or rolls back on failure.

The SQLAlchemy model metadata in `backend/app/models/` remains for Alembic schema creation and the development-only create-tables hook. It is not used to read or write application records. Keep schema changes in Alembic migrations; put runtime queries in `sql.properties`.

Run the API from `backend/` with `uvicorn app.main:app --reload`. Run backend tests with `python -m pytest tests`.
