from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.schema import CampaignCreate, CampaignUpdate, PaginatedFilter
from app.models.campaign import Campaign


async def create_campaign(db: AsyncSession, data: CampaignCreate) -> Campaign:
    """Insert a new campaign and return the created row with its generated id."""
    campaign = Campaign(**data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign

async def get_campaign(db: AsyncSession, campaign_id: int) -> Campaign | None:
    """Return a single campaign by id, or None if not found."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    return campaign

async def list_campaigns(db: AsyncSession, data: PaginatedFilter = None) -> list[Campaign]:
    """Return a paginated list of campaigns. Defaults to first page if no filter provided."""
    if data is None:
        data = PaginatedFilter()
    result = await db.execute(select(Campaign).offset(data.offset).limit(data.limit))
    campaigns = result.scalars().all()
    return list(campaigns)

async def get_total_number_of_campaigns(db: AsyncSession) -> int:
    """Return the total number of campaigns across all pages."""
    count = await db.execute(select(func.count()).select_from(Campaign))
    return int(count.scalar() or 0)

async def update_campaign(db: AsyncSession, campaign_id: int, data: CampaignUpdate) -> Campaign | None:
    """Update only the provided fields on a campaign. Returns None if not found."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        return None
    if data.name is not None:
        campaign.name = data.name
    if data.client is not None:
        campaign.client = data.client
    await db.commit()
    await db.refresh(campaign)
    return campaign

async def delete_campaign(db: AsyncSession, campaign_id: int) -> bool:
    """Delete a campaign by id. Returns True if deleted, False if not found."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        return False
    await db.delete(campaign)
    await db.commit()
    return True