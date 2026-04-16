# Campaign Tracker API

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (with Compose)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.11+

## First-time setup

**1. Clone the repo**
```bash
git clone <repo-url>
cd FastAPIProject
```

**2. Create your `.env` file**
```bash
cp .env.example .env
```

The default values work out of the box with Docker Compose — no changes needed.

**3. Start the stack**
```bash
docker compose up --build
```

This starts the API on `http://localhost:8000` and Postgres on port `5432`.

**4. Run migrations** (in a second terminal, while the stack is running)
```bash
docker compose exec api uv run alembic upgrade head
```

The API is now ready to accept requests.

## Example curl requests

**Create a campaign**
```bash
curl -s -X POST http://localhost:8000/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Launch", "client": "Acme"}' | jq
```

**Get a campaign**
```bash
curl -s http://localhost:8000/campaigns/1 | jq
```

## Running tests

Docker must be running (pytest-mock-resources spins up a real Postgres container).

```bash
uv run pytest tests/ -v
```

## Other commands

```bash
# Lint
uv run ruff check .

# Generate a migration after model changes
docker compose exec api uv run alembic revision --autogenerate -m "describe the change"

# Apply migrations
docker compose exec api uv run alembic upgrade head
```