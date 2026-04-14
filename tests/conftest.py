import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from pytest_mock_resources import create_postgres_fixture
from app.models.base import Base

from app.crud.campaign import create_campaign
from app.schema import CampaignCreate

pg = create_postgres_fixture(Base, async_=True)

"""
Build an async session from the pmr-managed engine.
Each test gets its own session; the container is reused across the suite.
"""
@pytest_asyncio.fixture
async def db_session(pg) -> AsyncSession:
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