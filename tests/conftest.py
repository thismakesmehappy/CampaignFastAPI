from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from pytest_mock_resources import create_postgres_fixture

from app.constants import PAGE_LIMIT_DEFAULT
from app.repositories import campaign as campaign_repo, metric as metric_repo
from app.models.base import Base

from app.schema import MetricCreate
from datetime import datetime, timezone

from app.models import Campaign, Metric, Client, User
from app.repositories import client as client_repo
from app.repositories import user as user_repo
from app.services.user import pwd_context

TEST_METRIC_SPEND = 1
TEST_METRIC_CLICKS = 2
TEST_METRIC_IMPRESSIONS = 3

LONG_STRING = "A" * 201

UPDATE_CAMPAIGN_NAME = "Update Campaign Name"
VALID_CAMPAIGN_NAME = "Test Campaign Name"
VALID_CLIENT_NAME = "Test Client"
VALID_CLIENT_API_KEY = "test-api-key"

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

@pytest.fixture
def make_client(db_session):
    """Factory fixture for creating clients."""
    async def _make(name="Acme", api_key=None):
        key = api_key or f"key-{name.lower().replace(' ', '-')}"
        return await client_repo.save(db_session, Client(name=name, api_key=key))
    return _make

@pytest.fixture
def make_campaign(db_session, make_client):
    """Factory fixture for creating campaigns with custom fields. Creates a client if not provided."""
    async def _make(name="Test Campaign", client_id=None, client_name="Acme"):
        if client_id is None:
            c = await make_client(name=client_name)
            client_id = c.id
        return await campaign_repo.save(db_session, Campaign(name=name, client_id=client_id))
    return _make

@pytest.fixture
def make_metric(db_session):
    """Factory fixture for creating metrics with custom fields."""
    async def _make(campaign_id, spend=0.0, clicks=0, impressions=0, period_start=PERIOD_START, period_end=PERIOD_END, source=None):
        kwargs = dict(spend=spend, clicks=clicks, impressions=impressions, period_start=period_start, period_end=period_end, campaign_id=campaign_id)
        if source is not None:
            kwargs["source"] = source
        return await metric_repo.save(db_session, Metric(**kwargs))

    return _make

@pytest.fixture
def campaign_factory(db_session):
    async def _make(name=VALID_CAMPAIGN_NAME, client_id=None):
        if client_id is None:
            c = await client_repo.save(db_session, Client(name="Default Client", api_key="default-key"))
            client_id = c.id
        return Campaign(name=name, client_id=client_id)
    return _make

@pytest_asyncio.fixture
async def existing_campaign(db_session, make_campaign):
    return await make_campaign()

@pytest_asyncio.fixture
async def existing_campaign_to_update(db_session, make_campaign):
    return await make_campaign()


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


@pytest_asyncio.fixture
async def existing_metrics(db_session, make_metric, make_campaign):
    campaign = await make_campaign()
    metrics = []
    for metric_data in TEST_METRIC_LIST:
        metric = await make_metric(campaign.id, spend=metric_data.spend, clicks=metric_data.clicks, impressions=metric_data.impressions, period_start=metric_data.period_start, period_end=metric_data.period_end)
        metrics.append(metric)
    return metrics


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

# Campaigns for metric filter tests:
# - 3x name="Test Campaign", client="Acme"       (default make_campaign)
# - 1x name="Other Campaign", client="Acme"      (different name, same client)
# - 1x name="Test Campaign", client="Other Client" (same name, different client)
# Total: 5 metrics
# Filter by name="Test":  4 results (3 default + 1 same-name-different-client)
# Filter by client="Acme": 4 results (3 default + 1 different-name-same-client)
# Filter by name="Test" AND client="Acme": 3 results (only the defaults)
@pytest_asyncio.fixture
async def existing_metrics_for_campaign_filter(db_session, make_metric, make_campaign, make_client):
    metrics = []
    campaign_ids = []
    acme = await make_client(name="Acme")
    for metric_data in TEST_METRICS_MULTI:
        campaign = await make_campaign(client_id=acme.id)
        metric = await make_metric(campaign.id, spend=metric_data.spend, clicks=metric_data.clicks, impressions=metric_data.impressions)
        metrics.append(metric)
        campaign_ids.append(campaign.id)
    # different name, same client (Acme)
    campaign = await make_campaign(name="Other Campaign", client_id=acme.id)
    metric = await make_metric(campaign.id, spend=4.4, clicks=4, impressions=40)
    metrics.append(metric)
    campaign_ids.append(campaign.id)
    # same name, different client
    other_client = await make_client(name="Other Client")
    campaign = await make_campaign(name="Test Campaign", client_id=other_client.id)
    metric = await make_metric(campaign.id, spend=5.5, clicks=5, impressions=50)
    metrics.append(metric)
    campaign_ids.append(campaign.id)
    client_ids = [acme.id, other_client.id]
    return {"metrics": metrics, "campaign_ids": campaign_ids, "client_ids": client_ids}

CAMPAIGN_LIST_NAMES = [
    ("Test Campaign Name One", "Test Campaign Client One"),
    ("Test Campaign Name Two", "Test Campaign Client Two"),
    ("Test Campaign Name Three", "Test Campaign Client Three"),
    ("Test Campaign Name Four", "Test Campaign Client Four"),
    ("Test Campaign Name Five", "Test Campaign Client Five"),
    ("Test Campaign Name Six", "Test Campaign Client Six"),
    ("Test Campaign Name Seven", "Test Campaign Client Seven"),
    ("Test Campaign Name Eight", "Test Campaign Client Eight"),
    ("Test Campaign Name Nine", "Test Campaign Client Nine"),
    ("Test Campaign Name Ten", "Test Campaign Client Ten"),
    ("Test Campaign Name Eleven", "Test Campaign Client Eleven"),
    ("Test Campaign Name Twelve", "Test Campaign Client Twelve"),
]

# Used only for name comparisons in tests — client_id is not meaningful here
TEST_CAMPAIGN_LIST = [Campaign(name=n, client_id=0) for n, _ in CAMPAIGN_LIST_NAMES]
# Parallel list of client names, matching TEST_CAMPAIGN_LIST order
TEST_CAMPAIGN_CLIENT_NAMES = [c for _, c in CAMPAIGN_LIST_NAMES]

@pytest_asyncio.fixture
async def existing_campaign_list(db_session):
    campaigns = []
    for name, client_name in CAMPAIGN_LIST_NAMES:
        c = await client_repo.save(db_session, Client(name=client_name, api_key=f"key-{client_name.lower().replace(' ', '-')}"))
        campaign = await campaign_repo.save(db_session, Campaign(name=name, client_id=c.id))
        campaigns.append(campaign)
    return campaigns

LENGTH_OF_RESULTS_DEFAULT_FILTERS = min(len(TEST_CAMPAIGN_LIST), PAGE_LIMIT_DEFAULT)

CLIENT_LIST_NAMES = [
    ("Acme Corp", "key-acme"),
    ("Beta Inc", "key-beta"),
    ("Gamma LLC", "key-gamma"),
    ("Delta Co", "key-delta"),
    ("Epsilon Ltd", "key-epsilon"),
    ("Zeta Group", "key-zeta"),
    ("Eta Ventures", "key-eta"),
    ("Theta Works", "key-theta"),
    ("Iota Systems", "key-iota"),
    ("Kappa Labs", "key-kappa"),
    ("Lambda Eleven", "key-lambda"),
    ("Mu Twelve", "key-mu"),
]

TEST_CLIENT_LIST = [Client(name=n, api_key=k) for n, k in CLIENT_LIST_NAMES]
LENGTH_OF_CLIENT_RESULTS_DEFAULT = min(len(CLIENT_LIST_NAMES), PAGE_LIMIT_DEFAULT)


@pytest.fixture
def client_factory():
    def _make(name=VALID_CLIENT_NAME, api_key=VALID_CLIENT_API_KEY):
        return Client(name=name, api_key=api_key)
    return _make


@pytest_asyncio.fixture
async def existing_client(db_session, client_factory):
    return await client_repo.save(db_session, client_factory())


@pytest_asyncio.fixture
async def existing_client_list(db_session):
    clients = []
    for name, api_key in CLIENT_LIST_NAMES:
        c = await client_repo.save(db_session, Client(name=name, api_key=api_key))
        clients.append(c)
    return clients


VALID_USERNAME = "test_user"
VALID_PASSWORD = "test-password-123"

USER_LIST_USERNAMES = [
    "user_one", "user_two", "user_three", "user_four", "user_five",
    "user_six", "user_seven", "user_eight", "user_nine", "user_ten",
    "user_eleven", "user_twelve",
]

LENGTH_OF_USER_RESULTS_DEFAULT = min(len(USER_LIST_USERNAMES), PAGE_LIMIT_DEFAULT)


@pytest.fixture
def make_user(db_session, make_client):
    """Factory fixture for creating users with custom fields. Creates a client if not provided. Password is hashed via the real pwd_context, same as production."""
    async def _make(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=None):
        if client_id is None:
            c = await make_client()
            client_id = c.id
        user = User(username=username, password_hash=pwd_context.hash(password), client_ids=[client_id], is_admin=False)
        return await user_repo.save(db_session, user)
    return _make


@pytest_asyncio.fixture
async def existing_user(db_session, make_user, existing_client):
    return await make_user(client_id=existing_client.id)


@pytest_asyncio.fixture
async def existing_user_list(db_session, make_user, existing_client):
    users = []
    for username in USER_LIST_USERNAMES:
        u = await make_user(username=username, client_id=existing_client.id)
        users.append(u)
    return users