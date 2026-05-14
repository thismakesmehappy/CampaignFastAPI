from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Client
from app.models.campaign import Campaign
from app.schema import PaginatedFilter
from app.schema.campaign import CampaignFilter
from app.repositories.base import save_with_generated_id

async def save(db: AsyncSession, campaign: Campaign) -> Campaign:
    return await save_with_generated_id(db, campaign)

async def get(db: AsyncSession, campaign_id: int) -> Campaign | None:
    """Return a single campaign by id, or None if not found."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    return campaign

def _apply_filters(query, options: CampaignFilter | None, client_id: int | None = None, sortable: bool = False):
    sort_by_options = {
        "client_name": Client.name,
        "name": Campaign.name,
        "created_at": Campaign.created_at,
        "id": Campaign.id
    }

    if options is None:
        options = CampaignFilter()

    needs_client_join = options.client_name_filter or (options.sort_by and "client_name" in options.sort_by_list)

    if needs_client_join:
        query = query.join(Client, Campaign.client_id == Client.id)

    query = query.where(Campaign.name.icontains(options.name_filter))

    if client_id is not None:
        query = query.where(Campaign.client_id == client_id)

    if options.client_name_filter:
        query = query.where(Client.name.icontains(options.client_name_filter))

    if options.id_list:
        query = query.where(Campaign.id.in_(options.id_list))

    if not sortable:
        return query

    for sort in options.sort_by_list:
        col = sort_by_options.get(sort)
        if not col:
            continue
        query = query.order_by(col.desc() if options.desc is not None else col)

    return query

async def find_all(db: AsyncSession, data: PaginatedFilter = None, options: CampaignFilter = None, client_id: int | None = None) -> list[Campaign]:
    """Return a paginated list of campaigns. Defaults to first page if no filter provided."""
    if data is None:
        data = PaginatedFilter()
    query = _apply_filters(select(Campaign), options, client_id, True).offset(data.offset).limit(data.limit)
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