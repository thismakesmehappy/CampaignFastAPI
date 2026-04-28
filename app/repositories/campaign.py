from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.campaign import Campaign
from app.schema import PaginatedFilter
from app.exceptions import DomainValidationError


async def save(db: AsyncSession, campaign: Campaign) -> Campaign:
    """Insert a new campaign and return the created row with its generated id."""
    try:
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign
    except SQLAlchemyError as e:
        await db.rollback()
        error = DomainValidationError()
        error.capture(str(e))
        raise error from e

async def get(db: AsyncSession, campaign_id: int) -> Campaign | None:
    """Return a single campaign by id, or None if not found."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    return campaign

async def find_all(db: AsyncSession, data: PaginatedFilter = None) -> list[Campaign]:
    """Return a paginated list of campaigns. Defaults to first page if no filter provided."""
    if data is None:
        data = PaginatedFilter()
    result = await db.execute(select(Campaign).offset(data.offset).limit(data.limit))
    campaigns = result.scalars().all()
    return list(campaigns)

async def count(db: AsyncSession) -> int:
    """Return the total number of campaigns across all pages."""
    result = await db.execute(select(func.count()).select_from(Campaign))
    return int(result.scalar() or 0)

async def delete(db: AsyncSession, campaign: Campaign) -> None:
    """Delete a campaign by id. Returns True if deleted, False if not found."""
    await db.delete(campaign)
    await db.commit()