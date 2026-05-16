# FastAPI + SQLAlchemy Async — Cheatsheet

---

## Infrastructure

| Tool | Why |
|---|---|
| **PostgreSQL 15** | Production-grade relational DB |
| **Docker Compose** | Runs Postgres locally without install |
| **Alembic** | Schema migrations (never rely on `create_all` in prod) |
| **uv** | Fast Python package manager, respects lockfile |

---

## Layer 1 — Models (`app/models/`) — SQLAlchemy ORM

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Numeric
from app.models.base import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped["Client"] = relationship(back_populates="campaigns")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="campaign")
    spend: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

- `Mapped[T]` — type-safe column (SQLAlchemy 2.x); `Mapped[T | None]` for nullable
- `mapped_column(primary_key=True)` — auto-increment int PK by default
- `ForeignKey("table.col")` — string reference to avoid circular imports
- `relationship(back_populates=...)` — both sides must declare it
- `Numeric(precision, scale)` — use for money/decimals, not `Float`

### `@property` on ORM models — computed, not stored

```python
class Campaign(Base):
    period_start: Mapped[date]
    period_end: Mapped[date]

    @property
    def duration_days(self) -> int:
        return (self.period_end - self.period_start).days
```

- Not a column — never written to the DB, not in migrations
- Accessible on any fetched ORM instance: `campaign.duration_days`
- To expose in a `Read` schema, just declare the field — `from_attributes=True` calls the property automatically:

```python
class CampaignRead(BaseModel):
    id: int
    duration_days: int             # Pydantic calls campaign.duration_days
    model_config = {"from_attributes": True}
```

---

## Layer 2 — Schemas (`app/schema/`) — Pydantic v2

```python
from pydantic import BaseModel, Field, model_validator, field_validator, computed_field

class MetricCreate(BaseModel):
    clicks: int = Field(ge=0)                  # >= 0
    spend: float = Field(ge=0)
    period_start: date
    period_end: date

    @model_validator(mode="after")             # runs after all fields are parsed
    def check_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be >= period_start")
        return self

class MetricRead(MetricCreate):
    id: int
    campaign_id: int
    model_config = {"from_attributes": True}   # deserialize from ORM objects

    @computed_field                            # included in .model_dump() and JSON response
    @property
    def ctr(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions

class MetricUpdate(BaseModel):
    clicks: int | None = None                  # all optional — PATCH semantics
    spend: float | None = None

class MetricFilter(BaseModel):                 # used as Depends() in routes
    campaign_name_filter: str | None = None
    id_list: list[int] | None = None

    @model_validator(mode="before")            # runs before field parsing, receives raw dict
    @classmethod
    def parse_ids(cls, v):                     # ?ids=1,2,3 → id_list=[1,2,3]
        if isinstance(v.get("ids"), str) and v["ids"]:
            v["id_list"] = [int(i) for i in v["ids"].split(",") if i.strip()]
        return v

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool
```

- `from_attributes = True` — lets Pydantic read ORM `.attr` directly (no `.dict()` needed)
- `Field(ge=0, le=100, min_length=1)` — inline validation constraints
- `model_validator(mode="before")` — raw dict input, good for parsing combined query params
- `model_validator(mode="after")` — typed object, good for cross-field checks
- `field_validator("field", mode="before")` — single-field transformation
- `@computed_field` + `@property` — included in serialization and OpenAPI schema (read-only)
- `Generic[T]` — parameterized schemas like `PaginatedResponse[MetricRead]`
- `model_dump(exclude_unset=True)` — only fields the caller actually sent (PATCH-safe)

---

## Layer 3 — Repositories (`app/repositories/`) — DB queries only

```python
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

async def find_all(db: AsyncSession, pagination, options=None):
    query = select(Metric).options(selectinload(Metric.campaign))  # eager load
    query = _apply_filters(query, options)
    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def count(db: AsyncSession, options=None) -> int:
    query = select(func.count()).select_from(Metric)
    query = _apply_filters(query, options)
    result = await db.execute(query)
    return result.scalar_one()

async def summarize(db: AsyncSession, options=None, ids=None):
    query = select(func.sum(Metric.clicks), func.sum(Metric.spend))
    if ids:
        query = query.where(Metric.id.in_(ids))
    result = await db.execute(query)
    return result.one()                        # one row, multiple columns

async def find_ids(db: AsyncSession, ids: list[int]) -> list[int]:
    result = await db.execute(select(Metric.id).where(Metric.id.in_(ids)))
    return list(result.scalars().all())        # scalars() on single-column = plain values

async def save(db: AsyncSession, obj) -> Metric:
    db.add(obj)
    await db.commit()
    await db.refresh(obj)                      # reload from DB (gets id, defaults, etc.)
    return obj

async def delete(db: AsyncSession, obj) -> None:
    await db.delete(obj)
    await db.commit()

def _apply_filters(query, options):
    if options is None:
        return query
    if options.id_list:
        query = query.where(Metric.id.in_(options.id_list))
    if options.campaign_name_filter:
        query = query.join(Metric.campaign).where(
            Campaign.name.ilike(f"%{options.campaign_name_filter}%")
        )
    return query
```

- `scalars().all()` — single-column result → `list[T]`; multi-column → use `.all()` or `.one()`
- `scalar_one()` — single value (count, sum); raises if no row
- `selectinload(Relation)` — eager-loads a relationship in a second query (avoids N+1)
- `joinedload(Relation)` — eager-loads via JOIN (better for to-one, can duplicate rows on to-many)
- `.ilike(f"%{val}%")` — case-insensitive LIKE
- `.in_(list)` — SQL `WHERE id IN (...)`
- `and_(cond1, cond2)` — explicit AND (implicit when chaining `.where()`)

---

## Layer 4 — Services (`app/services/`) — Business logic

```python
from app.exceptions import NotFoundError, DomainValidationError

async def create(db, campaign_id: int, data: MetricCreate) -> Metric:
    # validate_input  — reject bad inputs before any DB call
    # fetch           — load ORM objects
    campaign = await campaign_repo.get(db, campaign_id)
    # validate        — domain checks (existence, constraints)
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()
    # merge           — apply fields onto ORM object
    metric = Metric(campaign_id=campaign_id, **data.model_dump())
    # persist
    return await metric_repo.save(db, metric)

async def update(db, metric_id: int, data: MetricUpdate) -> Metric:
    metric = await metric_repo.get(db, metric_id)
    errors = NotFoundError()
    if metric is None:
        errors.capture("Metric")
    errors.raise_if_any()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(metric, field, value)
    error = DomainValidationError()
    if metric.period_end < metric.period_start:
        error.capture("period_end must be >= period_start")
    error.raise_if_any()
    return await metric_repo.save(db, metric)
```

Five-step template: **validate_input → fetch → validate → merge → persist**

- `model_dump(exclude_unset=True)` — only fields the caller sent (PATCH-safe)
- `errors.capture("X")` + `errors.raise_if_any()` — collect multiple errors before raising
- Never query the DB directly — always go through repositories

---

## Layer 5 — Routers (`app/routers/`) — HTTP only

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Path parameter
@router.get("/{metric_id}", response_model=MetricRead)
async def get_metric(
    metric_id: int,                            # from URL path segment
    db: AsyncSession = Depends(get_db),
):
    return await metric_service.get(db, metric_id)

# Query parameters (primitive)
@router.get("/summary")
async def summary(
    ids: str = Query(default=""),              # optional: ?ids=1,2,3
    ids: str = Query(...),                     # required: omitting → 422
    limit: int = Query(default=20, ge=1, le=100),
):
    ...

# Query parameters grouped via Depends
@router.get("/", response_model=PaginatedResponse[MetricRead])
async def list_metrics(
    pagination: PaginatedFilter = Depends(),   # FastAPI calls PaginatedFilter(**query_params)
    options: MetricFilter = Depends(),         # same — all query params available to both
    db: AsyncSession = Depends(get_db),
):
    return await metric_service.list_metrics(db, pagination, options=options)

# Request body
@router.post("/", response_model=MetricRead, status_code=201)
async def create_metric(
    data: MetricCreate,                        # JSON body — Pydantic parses + validates
    db: AsyncSession = Depends(get_db),
):
    return await metric_service.create(db, data)

# Custom error responses in OpenAPI docs
_404 = {404: {"description": "Not found"}}

@router.get("/{id}", responses=_404)
async def get(id: int, db=Depends(get_db)): ...
```

### Route ordering — static before dynamic

```python
router.get("/campaigns/metrics/summary")   # registered first
router.get("/campaigns/{campaign_id}")     # registered after
# reversed → "metrics" gets parsed as campaign_id
```

### Dependency injection — source by annotation

| Annotation | Source |
|---|---|
| `int`, `str` (bare, in path) | URL path segment |
| `Query(...)` / `Query(default=x)` | `?key=value` query string |
| `SomeModel` (no `= Depends()`) | JSON request body |
| `SomeModel = Depends()` | Query params → model constructor |
| `Depends(get_db)` | Runs `get_db()`, injects result |
| `Header(...)` | HTTP request header |

---

## Error Handling (`app/exceptions.py` + `app/error_handlers.py`)

```python
class AppError(Exception):
    def __init__(self):
        self.messages: list[str] = []

    def capture(self, message: str) -> None:   # accumulate errors
        self.messages.append(message)

    def raise_if_any(self) -> None:            # raise only if something was captured
        if self.messages:
            raise self

class NotFoundError(AppError):                 # → 404
    def capture(self, resource: str):          # auto-formats: "Campaign not found"
        self.messages.append(f"{resource} not found")

class DomainValidationError(AppError): ...     # → 422
class ConflictError(AppError): ...             # → 409
```

```python
def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"errors": exc.messages})

    @app.exception_handler(DomainValidationError)
    async def validation_handler(request, exc):
        return JSONResponse(status_code=422, content={"errors": exc.messages})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):
        return JSONResponse(status_code=409, content={"errors": exc.messages})
```

All errors respond with:
```json
{ "errors": ["Campaign not found", "Client not found"] }
```

### Where each exception is raised

| Exception | Step | Trigger |
|---|---|---|
| `NotFoundError` | `validate` | `repo.get()` returned `None` |
| `NotFoundError` | `validate` | `find_ids()` returned fewer ids than requested |
| `DomainValidationError` | `validate_input` | malformed/missing required params |
| `DomainValidationError` | `validate` (post-merge) | cross-field constraint (e.g. `period_end < period_start`) |
| `ConflictError` | `validate` | duplicate / state conflict |

- Never raise in repositories — repos return `None` for not-found; existence checks belong in services
- FastAPI's built-in 422 (Pydantic request parsing failure) fires before your route handler and uses a different response shape — `DomainValidationError` 422s are for business rule violations that require DB state

---

## Testing (`tests/`)

```python
# conftest.py — fixtures shared across all tests
@pytest_asyncio.fixture
async def db_session(pg):                      # pg = pmr-managed Postgres container
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session   # inject test DB
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

# Factory fixture — create seeded records
@pytest_asyncio.fixture
def make_metric(db_session):
    async def _make(campaign_id, **kwargs):
        m = Metric(campaign_id=campaign_id, clicks=kwargs.get("clicks", 1), ...)
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)
        return m
    return _make
```

### Test levels

| Level | Fixture | What to assert |
|---|---|---|
| Router | `client` | Status code, response JSON shape, error messages |
| Service | `db_session` | Return values, exceptions raised, side effects |
| Repository | `db_session` | Row counts, filter correctness, aggregate values |

```python
# Router test
async def test_create(client, make_campaign):
    campaign = await make_campaign()
    r = await client.post(f"/campaigns/{campaign.id}/metrics", json={"clicks": 5, ...})
    assert r.status_code == 201
    assert r.json()["clicks"] == 5

# Service test
async def test_not_found(db_session):
    with pytest.raises(NotFoundError):
        await metric_service.get(db_session, metric_id=999)

# Repository test
async def test_count_with_filter(db_session, make_metric):
    await make_metric(campaign_id=1)
    await make_metric(campaign_id=2)
    n = await metric_repo.count(db_session, options=MetricFilter(id_list=[1]))
    assert n == 1
```

- `asyncio_mode = "auto"` in `pyproject.toml` — no `@pytest.mark.asyncio` needed
- `pytest-mock-resources` spins up a real Postgres container — no mocking the DB