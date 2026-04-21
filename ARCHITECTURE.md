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

### Operation template

Every mutating operation follows the same sequence in the service layer:

1. **Validate inputs** — schema-level (Pydantic) handles field constraints; service handles cross-field and cross-resource rules
2. **Pull from store** — repository fetches current state
3. **Decorate / merge** — apply incoming changes to current state (for updates)
4. **Validate end state** — assert business invariants on the fully-merged object
5. **Persist** — repository writes the final state

### Example: update metric

```python
# app/services/metric.py
async def update_metric(db, metric_id: int, data: MetricUpdate) -> Metric:
    metric = await metric_repo.get(db, metric_id)       # 2. pull from store
    if metric is None:
        raise NotFoundError("Metric not found")

    merged = apply_update(metric, data)                 # 3. decorate / merge
    validate_period(merged.period_start, merged.period_end)  # 4. validate end state

    return await metric_repo.update(db, metric_id, merged)   # 5. persist
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

### Exception hierarchy

```python
# app/exceptions.py
class AppError(Exception): ...
class NotFoundError(AppError): ...
class DomainValidationError(AppError): ...
class ConflictError(AppError): ...
```

Routes catch `AppError` subclasses and map them to HTTP status codes. Domain code raises only domain exceptions — no `HTTPException` outside of routers.

---

## Target Directory Structure

```
app/
  routers/
    campaigns.py
    metrics.py
  services/
    campaign.py        # orchestration for campaign operations
    metric.py          # orchestration for metric operations
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
- Add `app/exceptions.py` with `NotFoundError`, `DomainValidationError`
- Update routers to catch domain exceptions instead of checking return values

### Phase 2 — Extract repositories
- Create `app/repositories/campaign.py` — move pure DB queries from `crud/campaign.py`
- Create `app/repositories/metric.py` — move pure DB queries from `crud/metric.py`
- Keep `crud/` as a compatibility shim during transition, then delete it

### Phase 3 — Introduce services
- Create `app/services/campaign.py` — move business logic from routes and crud
- Create `app/services/metric.py` — move business logic from routes and crud
- Routes call services; services call repositories

### Phase 4 — Thin the routes
- Routes should have no business logic — only HTTP concerns
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