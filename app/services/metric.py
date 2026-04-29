from app.repositories import campaign as campaign_repo, metric as metric_repo
from app.exceptions import NotFoundError, DomainValidationError
from app.models import Metric
from app.schema import (
    PaginatedResponse,
    PaginatedFilter,
    MetricRead,
    MetricSummary,
    MetricUpdate,
    MetricCreate,
)

async def create(db, campaign_id: int, data: MetricCreate) -> Metric:
    # validate_input
    # period order is validated in schema

    # fetch
    campaign = await campaign_repo.get(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    metric = Metric(campaign_id=campaign_id, impressions=data.impressions, clicks=data.clicks, spend=data.spend, period_start=data.period_start, period_end=data.period_end)

    # persist
    result = await metric_repo.save(db, metric)

    # return
    return result

async def get(db, metric_id) -> Metric:
    # validate_input
    # fetch
    metric = await metric_repo.get(db, metric_id)
    
    # validate
    errors = NotFoundError()
    if metric is None:
        errors.capture("Metric")
    errors.raise_if_any()

    # merge
    # persist
    # return
    return metric

async def list_metrics(db, pagination: PaginatedFilter, campaign_id: int | None = None) -> PaginatedResponse[MetricRead]:
    # validate_input
    # fetch
    campaign = None
    if campaign_id is not None:
        campaign = await campaign_repo.get(db, campaign_id)
    metrics = await metric_repo.find_all(db, pagination, campaign_id)
    total = await metric_repo.count(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign_id is not None and campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    has_more = pagination.offset + len(metrics) < total
    metrics_campaign = PaginatedResponse(items=metrics, total=total, limit=pagination.limit, has_more=has_more, offset=pagination.offset)

    # persist
    # return
    return metrics_campaign

async def list_metrics_summary(db, campaign_id: int | None = None) -> MetricSummary:
    # validate_input
    # fetch
    campaign = None
    if campaign_id is not None:
        campaign = await campaign_repo.get(db, campaign_id)
    aggregates = await metric_repo.summarize(db, campaign_id)
    total = await metric_repo.count(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign_id is not None and campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    result = MetricSummary(clicks=aggregates.clicks, impressions=aggregates.impressions, spend=aggregates.spend, total_metrics=total, campaign_id=campaign_id)

    # persist
    #return
    return result

async def update(db, metric_id: int, data: MetricUpdate) -> Metric:
    # validate_input
    # fetch
    metric = await metric_repo.get(db, metric_id)
    
    # validate
    errors = NotFoundError()
    if metric is None:
        errors.capture("Metric")
    errors.raise_if_any()
    
    # merge
    if data.clicks is not None:
        metric.clicks = data.clicks
    if data.impressions is not None:
        metric.impressions = data.impressions
    if data.spend is not None:
        metric.spend = data.spend
    if data.period_start is not None:
        metric.period_start = data.period_start
    if data.period_end is not None:
        metric.period_end = data.period_end

    # validate (post-merge)
    error = DomainValidationError()
    if metric.period_end < metric.period_start:
        error.capture("period_end must be greater or equal to period_start")
    error.raise_if_any()

    # persist
    result = await metric_repo.save(db, metric)

    # return
    return result

async def delete(db, metric_id: int) -> None:
    # validate_input
    # fetch
    metric = await metric_repo.get(db, metric_id)

    # validate
    errors = NotFoundError()
    if metric is None:
        errors.capture("Metric")
    errors.raise_if_any()

    # merge
    # persist
    await metric_repo.delete(db, metric)
    # return