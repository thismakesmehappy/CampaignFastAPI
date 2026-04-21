from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Metric
from app.schema import MetricBase, MetricCreate, MetricUpdate, PaginatedFilter


async def create_metric(db: AsyncSession, campaign_id: int, data: MetricCreate) -> Metric:
    """Insert a new metric and return the created row with its generated id."""
    metric = Metric(campaign_id=campaign_id, **data.model_dump())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric

async def get_metric(db: AsyncSession, metric_id: int) -> Metric | None:
    """Return a single metric by id, or None if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one_or_none()
    return metric

async def list_metrics(db: AsyncSession, data: PaginatedFilter = None, campaign_id: int | None = None) -> list[Metric]:
    """
    Return a paginated list of metrics. Defaults to first page if no filter provided.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    if data is None:
        data = PaginatedFilter()
    query = select(Metric)
    if campaign_id is not None:
        query = query.where(Metric.campaign_id == campaign_id)
    result = await db.execute(query.offset(data.offset).limit(data.limit))
    metrics = result.scalars().all()
    return list(metrics)

async def get_total_number_of_metrics(db: AsyncSession, campaign_id: int | None = None) -> int:
    """
    Return the total number of metric across all pages.
    If campaign_id is provided, limit count to metrics for that specific campaign.
    """
    query = select(func.count()).select_from(Metric)
    if campaign_id is not None:
        query = query.where(Metric.campaign_id == campaign_id)
    count = await db.execute(query)
    return int(count.scalar() or 0)

async def get_metrics_summary(db: AsyncSession, campaign_id: int | None = None) -> MetricBase:
    query = select(
        func.sum(Metric.clicks).label("clicks"),
        func.sum(Metric.impressions).label("impressions"),
        func.sum(Metric.spend).label("spend"),
    ).select_from(Metric)
    if campaign_id is not None:
        query = query.where(Metric.campaign_id == campaign_id)
    result = await db.execute(query)
    row = result.one()
    return MetricBase(clicks=row.clicks or 0, impressions=row.impressions or 0, spend=row.spend or 0)

async def update_metric(db: AsyncSession, metric_id: int, data: MetricUpdate) -> Metric | None:
    """Update only the provided fields on a metric. Returns None if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one_or_none()
    if metric is None:
        return None
    if data.spend is not None:
        metric.spend = data.spend
    if data.clicks is not None:
        metric.clicks = data.clicks
    if data.impressions is not None:
        metric.impressions = data.impressions
    if data.period_start is not None:
        metric.period_start = data.period_start
    if data.period_end is not None:
        metric.period_end = data.period_end

    if metric.period_end < metric.period_start:
        raise ValueError("period_end must be >= period_start")

    await db.commit()
    await db.refresh(metric)
    return metric

async def delete_metric(db: AsyncSession, metric_id: int) -> bool:
    """Delete a metric by id. Returns True if deleted, False if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one_or_none()
    if metric is None:
        return False
    await db.delete(metric)
    await db.commit()
    return True