from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Client
from app.models.campaign import Campaign
from app.schema import PaginatedFilter
from app.exceptions import DomainValidationError
from app.schema.campaign import CampaignFilter


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

def _apply_filters(query, options: CampaignFilter | None, client_id: int | None = None):
    if options is None:
        options = CampaignFilter()

    query = query.where(Campaign.name.icontains(options.name_filter))

    if client_id is not None:
        query = query.where(Campaign.client_id == client_id)

    if options.client_name_filter:
        query = query.join(Client, Campaign.client_id == Client.id).where(Client.name.icontains(options.client_name_filter))

    return query

async def find_all(db: AsyncSession, data: PaginatedFilter = None, options: CampaignFilter = None, client_id: int | None = None) -> list[Campaign]:
    """Return a paginated list of campaigns. Defaults to first page if no filter provided."""
    if data is None:
        data = PaginatedFilter()
    query = _apply_filters(select(Campaign), options, client_id).offset(data.offset).limit(data.limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def count(db: AsyncSession, options: CampaignFilter = None, client_id: int | None = None) -> int:
    """Return the total number of campaigns, respecting the same filters as find_all."""
    query = _apply_filters(select(func.count()).select_from(Campaign), options, client_id)
    result = await db.execute(query)
    return int(result.scalar() or 0)

async def delete(db: AsyncSession, campaign: Campaign) -> None:
    """Delete a campaign by id. Returns True if deleted, False if not found."""
    await db.delete(campaign)
    await db.commit()