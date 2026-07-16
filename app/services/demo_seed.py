import random
from datetime import datetime, timedelta, timezone

from app.auth import API_KEY_SYSTEM
from app.exceptions import NotFoundError
from app.repositories import client as client_repo
from app.repositories import metric as metric_repo
from app.schema import PaginatedFilter
from app.schema.campaign import CampaignCreate
from app.schema.demo_seed import SeedDemoDataRequest, SeedDemoDataResponse
from app.schema.metric import MetricCreate, MetricFilter
from app.services import campaign as campaign_service
from app.services import metric as metric_service

_CAMPAIGN_NAME_ADJECTIVES = ["Summer", "Spring", "Holiday", "Brand", "Retargeting", "Launch", "Flash", "Evergreen"]
_CAMPAIGN_NAME_NOUNS = ["Sale", "Awareness", "Promo", "Push", "Campaign", "Blitz"]

# Exclusive day-range bands matching the UI's filter pills (Today/7/30/60/90/180), each
# paired with the share of datapoint_count it gets when sparse. A band is (band_start, band_end]
# days ago, e.g. (7, 30] covers days 8-30. Each is checked independently so a client with only
# recent data still gets the older ranges filled in, and vice versa.
_RANGE_WEIGHTS = [
    (0, 7, 0.35),
    (7, 30, 0.30),
    (30, 60, 0.20),
    (60, 90, 0.10),
    (90, 180, 0.05),
]


def _bands_for(lookback_days: int) -> list[tuple[int, int, float]]:
    """Clip _RANGE_WEIGHTS to lookback_days, dropping bands entirely outside the window."""
    bands = []
    for band_start, band_end, weight in _RANGE_WEIGHTS:
        if band_start >= lookback_days:
            break
        bands.append((band_start, min(band_end, lookback_days), weight))
    return bands


async def _band_is_sparse(db, client_id: int, band_start: int, band_end: int, now: datetime) -> bool:
    period_start_floor = now - timedelta(days=band_end)
    period_start_ceiling = now - timedelta(days=band_start)
    options = MetricFilter(period_start=period_start_floor)
    count = await metric_repo.count(db, client_id=client_id, options=options)
    if count == 0:
        return True
    # count above only lower-bounds period_start; confirm at least one metric actually
    # falls inside this band (period_start <= ceiling) rather than in a later, larger band.
    metrics = await metric_repo.find_all(db, data=PaginatedFilter(limit=500), client_id=client_id, options=options)
    return not any(m.period_start <= period_start_ceiling for m in metrics)


def _random_campaign_name() -> str:
    return f"{random.choice(_CAMPAIGN_NAME_ADJECTIVES)} {random.choice(_CAMPAIGN_NAME_NOUNS)}"


def _random_metric_in_band(data: SeedDemoDataRequest, now: datetime, band_start: int, band_end: int) -> MetricCreate:
    days_ago = random.randint(band_start, band_end) if band_end > band_start else band_start
    period_end = now - timedelta(days=days_ago)
    period_start = period_end - timedelta(days=random.randint(0, 3))

    impressions = random.randint(data.min_impressions, data.max_impressions)
    clicks = random.randint(0, int(impressions * data.max_ctr))
    spend = round(random.uniform(data.min_spend, data.max_spend), 2)

    return MetricCreate(
        impressions=impressions,
        clicks=clicks,
        spend=spend,
        period_start=period_start,
        period_end=period_end,
    )


async def seed_demo_data(db, client_id: int, data: SeedDemoDataRequest) -> SeedDemoDataResponse:
    client = await client_repo.get(db, client_id)
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()

    now = datetime.now(timezone.utc)
    bands = _bands_for(data.lookback_days)
    sparse_bands = [b for b in bands if await _band_is_sparse(db, client_id, b[0], b[1], now)]

    if not sparse_bands:
        return SeedDemoDataResponse(seeded=False, campaigns_created=0, metrics_created=0, ranges_filled=[])

    campaigns = []
    for _ in range(data.campaign_count):
        campaign = await campaign_service.create(db, CampaignCreate(name=_random_campaign_name()), client_id)
        campaigns.append(campaign)

    metrics_created = 0
    for band_start, band_end, weight in sparse_bands:
        band_datapoints = max(1, round(data.datapoint_count * weight))
        for _ in range(band_datapoints):
            campaign = random.choice(campaigns)
            metric_data = _random_metric_in_band(data, now, band_start, band_end)
            await metric_service.create(db, campaign.id, metric_data, API_KEY_SYSTEM)
            metrics_created += 1

    return SeedDemoDataResponse(
        seeded=True,
        campaigns_created=len(campaigns),
        metrics_created=metrics_created,
        ranges_filled=[band_end for _, band_end, _ in sparse_bands],
    )