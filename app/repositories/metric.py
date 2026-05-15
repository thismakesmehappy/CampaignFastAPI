from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Metric, Client
from app.schema import MetricBase, PaginatedFilter
from app.models import Campaign
from app.schema.metric import MetricFilter, MetricSummaryWithId, MetricSummaryFilter
from app.repositories.base import save_with_generated_id, apply_sort


async def save(db: AsyncSession, metric: Metric) -> Metric:
    return await save_with_generated_id(db, metric)

async def get(db: AsyncSession, metric_id: int) -> Metric | None:
    """Return a single metric by id, or None if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one_or_none()
    return metric

def _apply_filters(query, options: MetricSummaryFilter | MetricFilter | None, sortable: bool = False, joined_campaign: bool = False, joined_client: bool = False):
    sort_by_options = {
        "client_name": Client.name,
        "campaign_name": Campaign.name,
        "impressions": Metric.impressions,
        "clicks": Metric.clicks,
        "spend": Metric.spend,
        "period_start": Metric.period_start,
        "period_end": Metric.period_end,
        "id": Metric.id,
        "created_at": Metric.created_at,
    }

    if options is None:
        return query

    needs_campaign_join = not joined_campaign and ("client_name" in options.sort_by_list or "campaign_name" in options.sort_by_list)
    if needs_campaign_join:
        query = query.join(Campaign, Metric.campaign_id == Campaign.id)
    needs_client_join = not joined_client and ("client_name" in options.sort_by_list)
    if needs_client_join:
        query = query.join(Client, Campaign.client_id == Client.id)

    if options.period_start is not None:
        query = query.where(Metric.period_start >= options.period_start)
    if options.period_end is not None:
        query = query.where(Metric.period_end <= options.period_end)
    if options.min_spend is not None:
        query = query.where(Metric.spend >= options.min_spend)
    if options.max_spend is not None:
        query = query.where(Metric.spend <= options.max_spend)
    if options.min_clicks is not None:
        query = query.where(Metric.clicks >= options.min_clicks)
    if options.max_clicks is not None:
        query = query.where(Metric.clicks <= options.max_clicks)
    if options.min_impressions is not None:
        query = query.where(Metric.impressions >= options.min_impressions)
    if options.max_impressions is not None:
        query = query.where(Metric.impressions <= options.max_impressions)

    return apply_sort(
        query,
        options.sort_by_list,
        sort_by_options,
        options.desc,
        sortable
    )

def _apply_relational_filters(query, campaign_id: int | None, client_id: int | None, options: MetricFilter | None, sortable: bool = False):
    if options is None:
        options = MetricFilter()
    if campaign_id is not None:
        query = query.where(Metric.campaign_id == campaign_id)

    needs_campaign_join = client_id is not None or options.campaign_name_filter or options.client_name_filter
    if needs_campaign_join:
        query = query.join(Campaign, Metric.campaign_id == Campaign.id)
    if client_id is not None:
        query = query.where(Campaign.client_id == client_id)
    if options.campaign_name_filter:
        query = query.where(Campaign.name.icontains(options.campaign_name_filter))
    needs_client_join = options.client_name_filter
    if needs_client_join:
        query = query.join(Client, Campaign.client_id == Client.id)
    if options.client_name_filter:
        query = query.where(Client.name.icontains(options.client_name_filter))

    return _apply_filters(query, options, sortable, needs_campaign_join, needs_client_join)

async def find_all(db: AsyncSession, data: PaginatedFilter = None, campaign_id: int | None = None, client_id: int | None = None, options: MetricFilter = None) -> list[Metric]:
    """
    Return a paginated list of metrics. Defaults to first page if no filter provided.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    if data is None:
        data = PaginatedFilter()

    query = _apply_relational_filters(select(Metric), campaign_id, client_id, options, True)
    result = await db.execute(query.offset(data.offset).limit(data.limit))
    metrics = result.scalars().all()
    return list(metrics)

async def count(db: AsyncSession, campaign_id: int | None = None, client_id: int | None = None, options: MetricSummaryFilter | None = None) -> int:
    """
    Return the total number of metric across all pages.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    full_options = MetricFilter.model_validate(options.model_dump()) if options else None
    query = _apply_relational_filters(select(func.count()).select_from(Metric), campaign_id, client_id, full_options)
    count = await db.execute(query)
    return int(count.scalar() or 0)

async def summarize(db: AsyncSession, options: MetricSummaryFilter | None = None) -> MetricBase:
    query = select(
        func.sum(Metric.clicks).label("clicks"),
        func.sum(Metric.impressions).label("impressions"),
        func.sum(Metric.spend).label("spend"),
    ).select_from(Metric)
    query = _apply_filters(query, options)
    result = await db.execute(query)
    row = result.one()
    return MetricBase(clicks=row.clicks or 0, impressions=row.impressions or 0, spend=row.spend or 0)

async def summarize_by_campaigns(db: AsyncSession, campaign_ids: list[int], options: MetricSummaryFilter = None) -> list[MetricSummaryWithId]:
    query = (
        select(
            Metric.campaign_id.label("id"),
            func.sum(Metric.clicks).label("clicks"),
            func.sum(Metric.impressions).label("impressions"),
            func.sum(Metric.spend).label("spend"),
            func.count(Metric.id).label("total_metrics"),
        )
        .where(Metric.campaign_id.in_(campaign_ids))
        )
    query = _apply_filters(query, options, True)
    query = query.group_by(Metric.campaign_id)
    result = await db.execute(query)
    return [MetricSummaryWithId.model_validate(row) for row in result.all()]


async def summarize_by_clients(db: AsyncSession, client_ids: list[int], options: MetricSummaryFilter = None) -> list[MetricSummaryWithId]:
    query = (
        select(
            Campaign.client_id.label("id"),
            func.sum(Metric.clicks).label("clicks"),
            func.sum(Metric.impressions).label("impressions"),
            func.sum(Metric.spend).label("spend"),
            func.count(Metric.id).label("total_metrics"),
        )
        .join(Campaign, Metric.campaign_id == Campaign.id)
        .where(Campaign.client_id.in_(client_ids))
    )
    query = _apply_filters(query, options, True, joined_campaign=True)
    query = query.group_by(Campaign.client_id)
    result = await db.execute(query)
    return [MetricSummaryWithId.model_validate(row) for row in result.all()]

async def delete(db: AsyncSession, metric: Metric) -> None:
    """Delete a metric by id. Returns True if deleted, False if not found."""
    await db.delete(metric)
    await db.commit()