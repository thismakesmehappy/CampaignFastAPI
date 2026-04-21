# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

| Layer | Tool |
|---|---|
| Web framework | FastAPI (async) |
| Data validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x async (`Mapped` / `mapped_column` syntax) |
| Migrations | Alembic |
| Database | PostgreSQL 15 (local via Docker Compose) |
| Settings | pydantic-settings (reads from `.env`) |
| Testing | pytest + pytest-asyncio + httpx + pytest-mock-resources |
| Linting | ruff (line-length 100) |
| Package manager | uv (lockfile: `uv.lock`, no `requirements.txt`) |

Python 3.11+ required — the codebase uses `Mapped`/`mapped_column` which is 3.10+ SQLAlchemy syntax.

## Commands

```bash
# Install deps (respects lockfile)
uv sync

# Run dev server (hot reload, DB must be up)
uv run uvicorn app.main:app --reload

# Start the full stack (API + Postgres)
docker compose up --build

# Lint
uv run ruff check .

# Run all tests (Docker must be running — pytest-mock-resources spins up a real Postgres container)
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/routers/test_campaigns.py -v

# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Project structure

```
app/
  main.py        # FastAPI app instance, lifespan hook (runs create_all on startup)
  database.py    # Async engine, SessionLocal, Base, get_db dependency
  constants.py   # Shared constants
  models/        # SQLAlchemy ORM models — base.py declares Base; one file per resource
  schema/        # Pydantic schemas — one file per resource, plus error.py and pagination.py
  crud/          # DB queries — one file per resource; routes call crud, never query directly
  routers/       # One file per resource group, each exports a router
alembic/
  versions/      # Auto-generated migration scripts
tests/
  conftest.py         # pg fixture (pmr-managed Postgres), db_session, async client
  routers/            # HTTP-level tests use `client` fixture
  crud/               # CRUD-level tests use `db_session` fixture directly
  helpers/            # Shared test factory helpers (e.g. creating seeded records)
.env                  # DATABASE_URL — not committed
```

## Architecture patterns

**Layering:** routes → crud → db. Routes handle HTTP concerns (status codes, dependency injection). `crud/` owns all `select`/`insert`/`update` statements. No raw queries in routers.

**Async everywhere:** engine, sessions, and all route handlers are async. Use `await db.execute(...)`, `await db.commit()`, `await db.refresh(obj)`.

**Dependency injection:** `get_db` in `database.py` yields an `AsyncSession` via FastAPI's `Depends`. Tests override this with `app.dependency_overrides[get_db]` to inject a test session backed by the pmr Postgres container.

**Schema/model split:** ORM models (in `app/models/`) are never returned directly from routes. Pydantic schemas (in `app/schema/`) handle serialization. `Read` schemas set `model_config = {"from_attributes": True}` to deserialize from ORM objects. Both packages re-export everything through their `__init__.py`.

**Migrations:** Alembic `env.py` imports `Base` from `app.models` and sets `target_metadata = Base.metadata`. After any model change, generate and apply a migration — don't rely on `create_all` in production (only used in the lifespan hook for dev convenience).

**Adding a new resource:** add an ORM model in `app/models/` (and re-export from `__init__.py`), Pydantic schemas in `app/schema/`, CRUD functions in `app/crud/`, a new router file in `app/routers/`, and register it with `app.include_router(...)` in `app/main.py`. Generate a migration.

## Testing

`pytest-mock-resources` pulls a real `postgres:15` container on first run and reuses it across the session. Each test gets an isolated schema (create_all → test → drop_all). Tests that hit routes use the `client` fixture; tests that exercise CRUD logic directly use `db_session`.

`asyncio_mode = "auto"` is set in `pyproject.toml` — no `@pytest.mark.asyncio` decorator needed on individual tests.