# Architecture

## Current State

The project uses a three-layer architecture:

```
routers/ → crud/ → db
```

| Layer | Location | Responsibility |
|---|---|---|
| HTTP | `app/routers/` | Request parsing, response serialization, status codes |
| Data access + business logic | `app/crud/` | DB queries AND business rules (mixed) |
| Schema | `app/schema/` | Input validation, response shapes |
| ORM | `app/models/` | Table definitions |

### Problems with this structure

- **Business logic is scattered.** Campaign existence checks live in routes. Period date validation lives in CRUD. Input constraints live in schemas. There is no single place to look for "what are the rules for creating a metric."
- **CRUD functions are doing two jobs.** `update_metric` fetches data, applies business rules, and persists — three distinct concerns in one function.
- **Routes are not thin.** Some routes assemble responses from multiple CRUD calls (e.g. list + count for pagination, summary + count for metric summary). This is orchestration logic that doesn't belong in the HTTP layer.
- **Errors are inconsistent.** Some layers raise `HTTPException`, others raise `ValueError`. The mapping between domain errors and HTTP status codes is implicit.

---

## Target State

A four-layer architecture modeled after the service/repository pattern:

```
routers/ → services/ → repositories/ → db
```

| Layer | Location | Responsibility |
|---|---|---|
| HTTP | `app/routers/` | HTTP only — parse request, call service, map exceptions to status codes |
| Orchestration | `app/services/` | Business rules, cross-resource coordination, operation sequencing |
| Data access | `app/repositories/` | Pure DB queries — no business logic, no validation |
| Schema | `app/schema/` | Contracts — input shapes, output shapes, field-level validation |
| ORM | `app/models/` | Table definitions |
| Exceptions | `app/exceptions.py` | Domain exception hierarchy |

---

## Operation Template

Every mutating operation in the service layer follows this four-step sequence:

### Steps

**1. `validate_input`** — fast, no DB calls
- Pydantic runs automatically before the service is called (FastAPI handles this)
- Add custom input rules here only if they cannot be expressed in Pydantic (rare)

**2. `decorate`** — all DB calls happen here and only here, in this order:
1. Fetch primary object — the thing being operated on; raise `NotFoundError` immediately if missing (precondition for everything else)
2. Fetch dependencies — related entities, counts, anything else needed for validation or persistence
3. Merge input — apply incoming data onto the primary object in place
4. Return context — bundle everything into the context dataclass

For **create** operations, skip step 1 (no primary object yet) and start with fetching dependencies.

**3. `validate`** — pure, no DB calls
- All business rules operate on the context object only
- Each rule is a separate private function
- Rules are registered in a list and executed in order by a `validate` orchestrator
- Raises `DomainValidationError` or `NotFoundError` on failure

**4. `persist`** — dumb, no logic
- Writes the primary object from context to the DB via the repository
- Returns the saved ORM object (with generated `id` for creates, refreshed state for updates)
- The service returns this result directly to the router; the router returns it to FastAPI which serializes it via the response model
- Nothing above `persist` needs to know how the ID was generated or how the object was refreshed

### Context objects

Each operation defines a context dataclass containing everything `validate` and `persist` need. The engineer decides what goes in it based on the rules being enforced.

```python
# app/services/metric.py
@dataclass
class MetricUpdateContext:
    metric: Metric           # current ORM object, merged with input
    campaign: Campaign       # fetched dependency
    metric_count: int        # fetched for limit validation
```

Context objects live inside the service file. They are not shared across services.

### Validator pattern

Each business rule is a named private function. Rules are registered in a list and run by the `validate` orchestrator:

```python
def _validate_period(ctx: MetricUpdateContext) -> None:
    if ctx.metric.period_end < ctx.metric.period_start:
        raise DomainValidationError("period_end must be >= period_start")

def _validate_metric_limit(ctx: MetricUpdateContext) -> None:
    if ctx.metric_count >= 100:
        raise DomainValidationError("Campaign cannot have more than 100 metrics")

_VALIDATORS = [
    _validate_period,
    _validate_metric_limit,
]

def validate(ctx: MetricUpdateContext) -> None:
    for validator in _VALIDATORS:
        validator(ctx)
```

Adding a new rule = one new function + one entry in `_VALIDATORS`. The `validate` orchestrator never changes.

### Example: update metric

```python
# app/services/metric.py

@dataclass
class MetricUpdateContext:
    metric: Metric
    campaign: Campaign
    metric_count: int

async def _decorate(db, metric_id: int, data: MetricUpdate) -> MetricUpdateContext:
    metric = await metric_repo.get(db, metric_id)
    if metric is None:
        raise NotFoundError("Metric not found")
    campaign = await campaign_repo.get(db, metric.campaign_id)
    metric_count = await metric_repo.count(db, metric.campaign_id)
    apply_update(metric, data)   # merge input into ORM object in place
    return MetricUpdateContext(metric=metric, campaign=campaign, metric_count=metric_count)

async def update_metric(db, metric_id: int, data: MetricUpdate) -> Metric:
    ctx = await _decorate(db, metric_id, data)
    validate(ctx)
    return await metric_repo.save(db, ctx.metric)
```

```python
# app/routers/metrics.py

@router.patch("/metrics/{metric_id}/")
async def update_metric(metric_id: int, data: MetricUpdate, db=Depends(get_db)):
    try:
        return await metric_service.update_metric(db, metric_id, data)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Metric not found")
    except DomainValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### Read operations

Read operations do not follow the mutating template — they have no decoration, validation, or persistence. Their structure is simple and self-evident, so a formal template would add ceremony without clarity.

**get** — fetch primary, raise if missing, return:
```python
async def get_metric(db, metric_id) -> Metric:
    metric = await metric_repo.get(db, metric_id)
    if metric is None:
        raise NotFoundError("Metric not found")
    return metric
```

**list** — fetch page, fetch total, assemble response, return:
```python
async def list_metrics(db, pagination, campaign_id=None) -> PaginatedResponse:
    items = await metric_repo.list(db, pagination, campaign_id)
    total = await metric_repo.count(db, campaign_id)
    return assemble_paginated(items, total, pagination)
```

**summary** — fetch aggregates, fetch total count, assemble response, return:
```python
async def get_metrics_summary(db, campaign_id=None) -> MetricSummary:
    aggregates = await metric_repo.summarize(db, campaign_id)
    total = await metric_repo.count(db, campaign_id)
    return MetricSummary(clicks=aggregates.clicks, impressions=aggregates.impressions, spend=aggregates.spend, total_metrics=total, campaign_id=campaign_id)
```

The pattern across all three: fetch everything needed, then assemble the response shape. The service owns response assembly — not the router.

---

## Exception Hierarchy

```python
# app/exceptions.py
class AppError(Exception):
    def __init__(self) -> None:
        self.messages = []

    def capture(self, message: str) -> None:
        self.messages.append(message)

    def raise_if_any(self) -> None:
        if self.messages:
            raise self

class NotFoundError(AppError):
    def capture(self, resource: str) -> None:
        self.messages.append(f"{resource} not found")

class DomainValidationError(AppError): ...

class ConflictError(AppError): ...
```

- Domain code (services, repositories) raises only `AppError` subclasses — never `HTTPException`
- Routes never catch exceptions — they just call the service and return
- Exception handlers registered in `main.py` catch `AppError` subclasses and map them to HTTP status codes
- The mapping between domain errors and HTTP status codes lives exclusively in `main.py`
- Each exception type accumulates all errors of that type before raising — errors are never mixed across types
- Errors are reported in sequential gates: input validation → not found → domain validation; each gate stops execution if it has errors
- `validate_input` and `validate` both raise `DomainValidationError` (422) — the distinction is when they run, not what they produce

```python
# service usage
errors = NotFoundError()
if not campaign:
    errors.capture("Campaign")
if not frequency_group:
    errors.capture("Frequency group")
errors.raise_if_any()
```

```python
# app/main.py
@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"errors": exc.messages})

@app.exception_handler(DomainValidationError)
async def validation_handler(request, exc):
    return JSONResponse(status_code=422, content={"errors": exc.messages})
```

```python
# app/routers/campaigns.py — no try/except needed
@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int, db=Depends(get_db)):
    return await campaign_service.get_campaign(db, campaign_id)
```

---

## Target Directory Structure

```
app/
  routers/
    campaigns.py
    metrics.py
  services/
    campaign.py        # operations for campaigns
    metric.py          # operations for metrics
  repositories/
    campaign.py        # pure DB queries for campaigns
    metric.py          # pure DB queries for metrics
  schema/
    campaign.py
    metric.py
    pagination.py
    error.py
  models/
    campaign.py
    metric.py
    base.py
  exceptions.py
  constants.py
  database.py
  main.py
tests/
  routers/             # HTTP-level integration tests (use client fixture)
  services/            # service-level tests (use db_session fixture)
  repositories/        # repository-level tests (use db_session fixture)
```

---

## Migration Plan

Refactor one resource at a time to avoid breaking changes. Campaigns first, then metrics.

### Phase 1 — Introduce exceptions
- Add `app/exceptions.py` with `NotFoundError`, `DomainValidationError`, `ConflictError`
- Update routers to raise domain exceptions (e.g. `NotFoundError`) when crud returns `None`, then catch and map to HTTP — crud does not change
- Update router tests to reflect new exception flow
- Add logging — configure in `main.py`, log exceptions in routers before mapping to HTTP

### Phase 2 — Extract repositories
- Create `app/repositories/campaign.py` — move pure DB queries from `crud/campaign.py`; repositories return `None` for missing resources, no exceptions
- Create `app/repositories/metric.py` — move pure DB queries from `crud/metric.py`
- Keep `crud/` as a compatibility shim during transition, then delete it
- Update tests: rename `tests/crud/` → `tests/repositories/`

### Phase 3 — Introduce services
- Create `app/services/campaign.py` — implement operation template for each mutating operation
- Create `app/services/metric.py` — implement operation template for each mutating operation
- Services check for `None` returns from repositories and raise domain exceptions (`NotFoundError`, `DomainValidationError`)
- Routes call services; services call repositories; routers only catch and map exceptions to HTTP
- Add `tests/services/` for service-level tests

### Phase 4 — Thin the routes
- Routes contain only: parse request → call service → map exception → return response
- All orchestration (multi-repo calls, response assembly) moves to services

---

## API Versioning

Planned: header-based versioning via a custom `API-Version` header.

```
API-Version: 1   # default, current behavior
API-Version: 2   # future breaking changes
```

A FastAPI dependency reads the header and returns the version. Routes dispatch to versioned service calls where behavior differs. Non-breaking additions (new fields, new endpoints) do not require a version bump.

This approach was chosen over URL versioning (`/v1/metrics/`) to keep URLs stable, and over `Accept` header versioning for discoverability and ease of testing.
