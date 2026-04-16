from typing import Any, AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from pytest_mock_resources import create_postgres_fixture

from app.crud.metric import create_metric
from app.models.base import Base

from app.crud.campaign import create_campaign
from app.schema import CampaignCreate, MetricCreate

pg = create_postgres_fixture(Base, async_=True)



"""
Build an async session from the pmr-managed engine.
Each test gets its own session; the container is reused across the suite.
"""
@pytest_asyncio.fixture
async def db_session(pg) -> AsyncGenerator[AsyncSession, Any]:
    async with pg.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(pg, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with pg.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

'''
Factory for parameterized campaigns to be used in testt that required putting campaigns in the database
'''
@pytest_asyncio.fixture
def make_campaign(db_session):
    async def _make(name="Test Campaign", client="Acme"):
        return await create_campaign(db_session, CampaignCreate(name=name, client=client))

    return _make

'''
Factory for parameterized metrics to be used in testt that required putting campaigns in the database
'''
@pytest_asyncio.fixture
def make_metric(db_session):
    async def _make(campaign_id, spend=0, clicks=0, impressions=0):
        return await create_metric(db_session, campaign_id, MetricCreate(spend=spend, clicks=clicks, impressions=impressions))

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