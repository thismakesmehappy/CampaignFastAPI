from typing import Any, AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from pytest_mock_resources import create_postgres_fixture

from app.constants import PAGE_LIMIT_DEFAULT
from app.crud.metric import create_metric
from app.models.base import Base

from app.crud.campaign import create_campaign
from app.schema import CampaignCreate, MetricBase

LONG_STRING = "A" * 201

UPDATE_CAMPAIGN_NAME = "Update Campaign Name"
UPDATE_CAMPAIGN_CLIENT = "Update Campaign Client"
VALID_CAMPAIGN_NAME = "Test Campaign Name"
VALID_CAMPAIGN_CLIENT = "Test Campaign Client"

TEST_METRIC = MetricBase(spend=100.0, clicks=50, impressions=1000)
UPDATE_METRIC_SPEND = 200.0
UPDATE_METRIC_CLICKS = 75
UPDATE_METRIC_IMPRESSIONS = 2000

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
        return await create_campaign(db_session, CampaignCreate(name=name, client=client))

    return _make

@pytest_asyncio.fixture
def make_metric(db_session):
    """Factory fixture for creating metrics with custom fields."""
    async def _make(campaign_id, spend=0, clicks=0, impressions=0):
        return await create_metric(db_session, campaign_id, MetricBase(spend=spend, clicks=clicks, impressions=impressions))

    return _make

async def make_campaign_list(db_session: AsyncSession, campaigns_to_build: list[CampaignCreate]) -> list[Any]:
    campaigns = []
    for test_campaign in campaigns_to_build:
        campaign = await create_campaign(db_session, test_campaign)
        campaigns.append(campaign)
    return campaigns

TEST_CAMPAIGN = CampaignCreate(name="Test Campaign Name", client="Test Campaign Client")

@pytest_asyncio.fixture
async def existing_campaign(db_session):
    return await create_campaign(db_session, TEST_CAMPAIGN)


@pytest_asyncio.fixture
async def existing_metric(db_session, existing_campaign):
    return await create_metric(db_session, existing_campaign.id, TEST_METRIC)


TEST_METRIC_LIST = [
    MetricBase(spend=float(i * 10), clicks=i * 5, impressions=i * 100)
    for i in range(1, 13)
]


async def make_metric_list(db_session: AsyncSession, campaign_id: int, metrics_to_build: list[MetricBase]) -> list[Any]:
    metrics = []
    for metric_data in metrics_to_build:
        metric = await create_metric(db_session, campaign_id, metric_data)
        metrics.append(metric)
    return metrics


@pytest_asyncio.fixture
async def existing_metric_list(db_session, existing_campaign):
    return await make_metric_list(db_session, existing_campaign.id, TEST_METRIC_LIST)


LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS = min(len(TEST_METRIC_LIST), PAGE_LIMIT_DEFAULT)

TEST_CAMPAIGNS_MULTI = [
    CampaignCreate(name="Test Campaign Name 1", client="Test Campaign Client 1"),
    CampaignCreate(name="Test Campaign Name 2", client="Test Campaign Client 2"),
    CampaignCreate(name="Test Campaign Name 3", client="Test Campaign Client 3"),
]

TEST_METRICS_MULTI = [
    MetricBase(spend=1.1, clicks=1, impressions=10),
    MetricBase(spend=2.2, clicks=2, impressions=20),
    MetricBase(spend=3.3, clicks=3, impressions=30),
]

SUMMARY_TOTAL_SPEND = sum(m.spend for m in TEST_METRICS_MULTI)
SUMMARY_TOTAL_CLICKS = sum(m.clicks for m in TEST_METRICS_MULTI)
SUMMARY_TOTAL_IMPRESSIONS = sum(m.impressions for m in TEST_METRICS_MULTI)


@pytest_asyncio.fixture
async def existing_metrics_across_campaigns(db_session):
    """One metric per campaign across multiple campaigns. Use to test campaign-scoped filtering."""
    campaigns = await make_campaign_list(db_session, TEST_CAMPAIGNS_MULTI)
    campaign_ids = [campaign.id for campaign in campaigns]
    metrics = []
    for index in range(len(TEST_METRICS_MULTI)):
        metric = await create_metric(db_session, campaign_ids[index], TEST_METRICS_MULTI[index])
        metrics.append(metric)
    return {"metrics": metrics, "campaign_ids": campaign_ids}

TEST_CAMPAIGN_LIST = [
    CampaignCreate(name="Test Campaign Name 1", client="Test Campaign Client 1"),
    CampaignCreate(name="Test Campaign Name 2", client="Test Campaign Client 2"),
    CampaignCreate(name="Test Campaign Name 3", client="Test Campaign Client 3"),
    CampaignCreate(name="Test Campaign Name 4", client="Test Campaign Client 4"),
    CampaignCreate(name="Test Campaign Name 5", client="Test Campaign Client 5"),
    CampaignCreate(name="Test Campaign Name 6", client="Test Campaign Client 6"),
    CampaignCreate(name="Test Campaign Name 7", client="Test Campaign Client 7"),
    CampaignCreate(name="Test Campaign Name 8", client="Test Campaign Client 8"),
    CampaignCreate(name="Test Campaign Name 9", client="Test Campaign Client 9"),
    CampaignCreate(name="Test Campaign Name 10", client="Test Campaign Client 10"),
    CampaignCreate(name="Test Campaign Name 11", client="Test Campaign Client 11"),
    CampaignCreate(name="Test Campaign Name 12", client="Test Campaign Client 12")
]

@pytest_asyncio.fixture
async def existing_campaign_list(db_session):
    return await make_campaign_list(db_session, TEST_CAMPAIGN_LIST)

LENGTH_OF_RESULTS_DEFAULT_FILTERS = min(len(TEST_CAMPAIGN_LIST), PAGE_LIMIT_DEFAULT)
