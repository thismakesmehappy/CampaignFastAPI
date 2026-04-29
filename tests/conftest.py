from typing import Any, AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from pytest_mock_resources import create_postgres_fixture

from app.constants import PAGE_LIMIT_DEFAULT
from app.repositories import campaign as campaign_repo, metric as metric_repo
from app.models.base import Base

from app.schema import MetricCreate
from datetime import datetime, timezone

from app.models import Campaign
from app.models import Metric

TEST_METRIC_SPEND = 1
TEST_METRIC_CLICKS = 2
TEST_METRIC_IMPRESSIONS = 3

LONG_STRING = "A" * 201

UPDATE_CAMPAIGN_NAME = "Update Campaign Name"
UPDATE_CAMPAIGN_CLIENT = "Update Campaign Client"
VALID_CAMPAIGN_NAME = "Test Campaign Name"
VALID_CAMPAIGN_CLIENT = "Test Campaign Client"

PERIOD_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 1, 31, tzinfo=timezone.utc)

TEST_METRIC = MetricCreate(spend=100.0, clicks=50, impressions=1000, period_start=PERIOD_START, period_end=PERIOD_END)
UPDATE_METRIC_SPEND = 200.0
UPDATE_METRIC_CLICKS = 75
UPDATE_METRIC_IMPRESSIONS = 2000
UPDATE_METRIC_PERIOD_START = datetime(2026, 2, 2, tzinfo=timezone.utc)
UPDATE_METRIC_PERIOD_END = datetime(2026, 3, 3, tzinfo=timezone.utc)

pg = create_postgres_fixture(Base, async_=True)

@pytest_asyncio.fixture
async def db_session(pg) -> AsyncGenerator[AsyncSession, Any]:
    """Build an async session from the pmr-managed engine. Each test gets its own isolated schema."""
    async with pg.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(pg, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with pg.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
def make_campaign(db_session):
    """Factory fixture for creating campaigns with custom fields."""
    async def _make(name="Test Campaign", client="Acme"):
        return await campaign_repo.save(db_session, Campaign(name=name, client=client))

    return _make

@pytest_asyncio.fixture
def make_metric(db_session):
    """Factory fixture for creating metrics with custom fields."""
    async def _make(campaign_id, spend=0.0, clicks=0, impressions=0, period_start=PERIOD_START, period_end=PERIOD_END):
        return await metric_repo.save(db_session, Metric(spend=spend, clicks=clicks, impressions=impressions, period_start=period_start, period_end=period_end, campaign_id=campaign_id))

    return _make

async def make_campaign_list(db_session: AsyncSession, campaigns_to_build: list[Campaign]) -> list[Any]:
    campaigns = []
    for test_campaign in campaigns_to_build:
        campaign = await campaign_repo.save(db_session, test_campaign)
        campaigns.append(campaign)
    return campaigns

@pytest_asyncio.fixture
def campaign_factory():
    def _make(name=VALID_CAMPAIGN_NAME, client=VALID_CAMPAIGN_CLIENT):
        return Campaign(name=name, client=client)
    return _make

@pytest_asyncio.fixture
async def existing_campaign(db_session, campaign_factory):
    return await campaign_repo.save(db_session, campaign_factory())

@pytest_asyncio.fixture
async def existing_campaign_to_update(db_session, campaign_factory):
    return await campaign_repo.save(db_session, campaign_factory())


@pytest_asyncio.fixture
async def existing_metric(db_session, make_metric, make_campaign):
    campaign = await make_campaign()
    return await make_metric(campaign.id, spend=TEST_METRIC_SPEND, clicks=TEST_METRIC_CLICKS, impressions=TEST_METRIC_IMPRESSIONS)


TEST_METRIC_LIST = [
    MetricCreate(
        spend=float(i * 10),
        clicks=i * 5,
        impressions=i * 100,
        period_start=datetime(2026, 1, i, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, i, tzinfo=timezone.utc),
    )
    for i in range(1, 13)
]


@pytest_asyncio.fixture
async def existing_metric_list(db_session, make_metric, make_campaign):
    campaign = await make_campaign()
    for metric_data in TEST_METRIC_LIST:
        await make_metric(campaign.id, spend=metric_data.spend, clicks=metric_data.clicks, impressions=metric_data.impressions, period_start=metric_data.period_start, period_end=metric_data.period_end)
    return campaign


LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS = min(len(TEST_METRIC_LIST), PAGE_LIMIT_DEFAULT)

TEST_METRICS_MULTI = [
    MetricCreate(spend=1.1, clicks=1, impressions=10, period_start=datetime(2026, 1, 1, tzinfo=timezone.utc), period_end=datetime(2026, 1, 1, tzinfo=timezone.utc)),
    MetricCreate(spend=2.2, clicks=2, impressions=20, period_start=datetime(2026, 1, 2, tzinfo=timezone.utc), period_end=datetime(2026, 1, 2, tzinfo=timezone.utc)),
    MetricCreate(spend=3.3, clicks=3, impressions=30, period_start=datetime(2026, 1, 3, tzinfo=timezone.utc), period_end=datetime(2026, 1, 3, tzinfo=timezone.utc)),
]

SUMMARY_TOTAL_SPEND = sum(m.spend for m in TEST_METRICS_MULTI)
SUMMARY_TOTAL_CLICKS = sum(m.clicks for m in TEST_METRICS_MULTI)
SUMMARY_TOTAL_IMPRESSIONS = sum(m.impressions for m in TEST_METRICS_MULTI)


@pytest_asyncio.fixture
async def existing_metrics_single_campaign(db_session, make_metric, make_campaign):
    """Multiple metrics for a single campaign. Use to test aggregation (e.g. summary SUM)."""
    campaign = await make_campaign()
    for metric in TEST_METRICS_MULTI:
        await make_metric(campaign.id, spend=metric.spend, clicks=metric.clicks, impressions=metric.impressions)
    return campaign

@pytest_asyncio.fixture
async def existing_metrics_across_campaigns(db_session, make_metric, make_campaign):
    """One metric per campaign across multiple campaigns. Use to test campaign-scoped filtering."""
    metrics = []
    campaign_ids = []
    for metric_data in TEST_METRICS_MULTI:
        campaign = await make_campaign()
        metric = await make_metric(campaign.id, spend=metric_data.spend, clicks=metric_data.clicks, impressions=metric_data.impressions)
        metrics.append(metric)
        campaign_ids.append(campaign.id)
    return {"metrics": metrics, "campaign_ids": campaign_ids}

CAMPAIGN_LIST_NAMES = [
    ("Test Campaign Name 1", "Test Campaign Client 1"),
    ("Test Campaign Name 2", "Test Campaign Client 2"),
    ("Test Campaign Name 3", "Test Campaign Client 3"),
    ("Test Campaign Name 4", "Test Campaign Client 4"),
    ("Test Campaign Name 5", "Test Campaign Client 5"),
    ("Test Campaign Name 6", "Test Campaign Client 6"),
    ("Test Campaign Name 7", "Test Campaign Client 7"),
    ("Test Campaign Name 8", "Test Campaign Client 8"),
    ("Test Campaign Name 9", "Test Campaign Client 9"),
    ("Test Campaign Name 10", "Test Campaign Client 10"),
    ("Test Campaign Name 11", "Test Campaign Client 11"),
    ("Test Campaign Name 12", "Test Campaign Client 12"),
]

TEST_CAMPAIGN_LIST = [Campaign(name=n, client=c) for n, c in CAMPAIGN_LIST_NAMES]

@pytest_asyncio.fixture
async def existing_campaign_list(db_session):
    return await make_campaign_list(db_session, [Campaign(name=n, client=c) for n, c in CAMPAIGN_LIST_NAMES])

LENGTH_OF_RESULTS_DEFAULT_FILTERS = min(len(TEST_CAMPAIGN_LIST), PAGE_LIMIT_DEFAULT)