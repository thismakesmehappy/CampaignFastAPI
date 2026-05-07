from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Metric
from app.schema import MetricBase, PaginatedFilter
from app.exceptions import DomainValidationError
from app.models import Campaign
from app.schema.metric import MetricFilter


async def save(db: AsyncSession, metric: Metric) -> Metric:
    """Insert a new metric and return the created row with its generated id."""
    try:
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        return metric
    except SQLAlchemyError as e:
        await db.rollback()
        error = DomainValidationError()
        error.capture(str(e))
        raise error from e

async def get(db: AsyncSession, metric_id: int) -> Metric | None:
    """Return a single metric by id, or None if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one_or_none()
    return metric

def _apply_filters(query, campaign_id: int | None, options: MetricFilter | None):
    if options is None:
        options = MetricFilter()
    if campaign_id is not None:
        query = query.where(Metric.campaign_id == campaign_id)

    if options.campaign_name_filter or options.campaign_client_filter:
        query = query.join(Campaign, Metric.campaign_id == Campaign.id)
        query = query.where(Campaign.name.icontains(options.campaign_name_filter))
        query = query.where(Campaign.client.icontains(options.campaign_client_filter))

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

    return query

async def find_all(db: AsyncSession, data: PaginatedFilter = None, campaign_id: int | None = None, options: MetricFilter = None) -> list[Metric]:
    """
    Return a paginated list of metrics. Defaults to first page if no filter provided.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    if data is None:
        data = PaginatedFilter()

    query = _apply_filters(select(Metric), campaign_id, options)
    result = await db.execute(query.offset(data.offset).limit(data.limit))
    metrics = result.scalars().all()
    return list(metrics)

async def count(db: AsyncSession, campaign_id: int | None = None, options: MetricFilter | None = None) -> int:
    """
    Return the total number of metric across all pages.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    query = _apply_filters(select(func.count()).select_from(Metric), campaign_id, options)
    count = await db.execute(query)
    return int(count.scalar() or 0)

async def summarize(db: AsyncSession, campaign_id: int | None = None, options: MetricFilter | None = None) -> MetricBase:
    query = select(
        func.sum(Metric.clicks).label("clicks"),
        func.sum(Metric.impressions).label("impressions"),
        func.sum(Metric.spend).label("spend"),
    ).select_from(Metric)
    query = _apply_filters(query, campaign_id, options)
    result = await db.execute(query)
    row = result.one()
    return MetricBase(clicks=row.clicks or 0, impressions=row.impressions or 0, spend=row.spend or 0)

async def delete(db: AsyncSession, metric: Metric) -> None:
    """Delete a metric by id. Returns True if deleted, False if not found."""
    await db.delete(metric)
    await db.commit()