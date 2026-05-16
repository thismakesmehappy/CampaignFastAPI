from app.repositories import campaign as campaign_repo, metric as metric_repo, client as client_repo
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
from app.schema.metric import (
    MetricFilter,
    MetricSummaryFilter,
    MetricSummaryList,
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

async def list_metrics(db, pagination: PaginatedFilter = None, campaign_id: int | None = None, client_id: int | None = None, options: MetricFilter | None = None) -> PaginatedResponse[MetricRead]:
    # validate_input
    if pagination is None:
        pagination = PaginatedFilter()
    # fetch
    campaign = None
    if campaign_id is not None:
        campaign = await campaign_repo.get(db, campaign_id)
    client = None
    if client_id is not None:
        client = await client_repo.get(db, client_id)

    # validate
    errors = NotFoundError()
    if campaign_id is not None and campaign is None:
        errors.capture("Campaign")
    if client_id is not None and client is None:
        errors.capture("Client")
    errors.raise_if_any()

    # fetch_metrics
    metrics = await metric_repo.find_all(db, pagination, campaign_id, client_id, options)
    total = await metric_repo.count(db, campaign_id, client_id, options)

    # validate ids
    if options and options.id_list:
        found_ids = {m.id for m in metrics}
        errors = NotFoundError()
        for id_ in options.id_list:
            if id_ not in found_ids:
                errors.capture(f"Metric {id_}")
        errors.raise_if_any()

    # merge
    has_more = pagination.offset + len(metrics) < total
    metrics_campaign = PaginatedResponse(items=metrics, total=total, limit=pagination.limit, has_more=has_more, offset=pagination.offset)

    # persist
    # return
    return metrics_campaign

async def metrics_summary(db, ids: str = "", options: MetricSummaryFilter | None = None) -> MetricSummary:
    # validate_input
    metric_ids = [int(i) for i in ids.split(",") if i.strip()] if ids else []

    # fetch / validate ids if provided
    if metric_ids:
        found = await metric_repo.find_ids(db, metric_ids)
        if len(found) < len(metric_ids):
            errors = NotFoundError()
            for id_ in metric_ids:
                if id_ not in found:
                    errors.capture(f"Metric {id_}")
            errors.raise_if_any()

    # fetch_metrics_summary
    count_options = MetricFilter(**(options.model_dump() if options else {}), ids=ids) if metric_ids else options
    aggregates = await metric_repo.summarize(db, options=options, ids=metric_ids or None)
    total = await metric_repo.count(db, options=count_options)

    # merge
    result = MetricSummary(clicks=aggregates.clicks, impressions=aggregates.impressions, spend=aggregates.spend, total_metrics=total)

    # persist
    # return
    return result

async def metrics_summary_for_campaigns(db, ids: str, options: MetricSummaryFilter | None = None) -> MetricSummaryList:
    # validate_input
    errors = DomainValidationError()
    if not ids:
        errors.capture("ids URL parameters must be non-empty")
    errors.raise_if_any()
    campaign_ids = [int(i) for i in ids.split(",")]

    # fetch
    found = await campaign_repo.find_ids(db, campaign_ids)

    # validate
    if len(found) < len(campaign_ids):
        errors = NotFoundError()
        for id_ in campaign_ids:
            if id_ not in found:
                errors.capture(f"Campaign {id_}")
        errors.raise_if_any()

    # fetch_metrics_summary_for_campaigns
    summaries = await metric_repo.summarize_by_campaigns(db, campaign_ids, options)

    # merge
    result = MetricSummaryList(resource_type="campaign", summaries=summaries)

    # persist
    # return
    return result

async def metrics_summary_for_clients(db, ids: str, options: MetricSummaryFilter | None = None) -> MetricSummaryList:
    # validate_input
    errors = DomainValidationError()
    if not ids:
        errors.capture("ids URL parameters must be non-empty")
    errors.raise_if_any()
    client_ids = [int(i) for i in ids.split(",")]

    # fetch
    found = await client_repo.find_ids(db, client_ids)

    # validate
    if len(found) < len(client_ids):
        errors = NotFoundError()
        for id_ in client_ids:
            if id_ not in found:
                errors.capture(f"Client {id_}")
        errors.raise_if_any()

    # fetch_metrics_summary_for_clients
    summaries = await metric_repo.summarize_by_clients(db, client_ids, options)

    # merge
    result = MetricSummaryList(resource_type="client", summaries=summaries)

    # persist
    # return
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