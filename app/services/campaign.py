from app.repositories import campaign as campaign_repo
from app.repositories import client as client_repo
from app.exceptions import NotFoundError
from app.models import Campaign
from app.schema import CampaignCreate, PaginatedFilter, PaginatedResponse, CampaignUpdate
from app.schema.campaign import CampaignFilter


async def create(db, data: CampaignCreate, client_id: int) -> Campaign:
    # validate_input
    # fetch
    client = await client_repo.get(db, client_id)

    # validate
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()

    # merge
    campaign = Campaign(name=data.name, client_id=client_id)

    # persist
    result = await campaign_repo.save(db, campaign)

    # return
    return result

async def get(db, campaign_id) -> Campaign:
    # validate_input
    # fetch
    campaign = await campaign_repo.get(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    # return
    return campaign

async def list_campaigns(db, pagination: PaginatedFilter = None, options: CampaignFilter = None, client_id: int | None = None):
    # validate_input
    if pagination is None:
        pagination = PaginatedFilter()
    # fetch
    client = None
    if client_id is not None:
        client = await client_repo.get(db, client_id)

    # validate
    errors = NotFoundError()
    if client_id is not None and client is None:
        errors.capture("Client")
    errors.raise_if_any()

    # fetch campaigns
    campaigns_list = await campaign_repo.find_all(db, pagination, options, client_id)
    total = await campaign_repo.count(db, options, client_id)

    # merge
    has_more = pagination.offset + len(campaigns_list) < total
    response = PaginatedResponse(items=campaigns_list, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)

    # return
    return response

async def update(db, campaign_id: int, data: CampaignUpdate):
    # validate_input
    # fetch
    campaign = await campaign_repo.get(db, campaign_id)
    client = await client_repo.get(db, data.client_id) if data.client_id is not None else None

    # validate
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    if data.client_id is not None and client is None:
        errors.capture("Client")
    errors.raise_if_any()

    # merge
    if data.name is not None:
        campaign.name = data.name
    if data.client_id is not None:
        campaign.client_id = data.client_id

    # persist
    result = await campaign_repo.save(db, campaign)

    # return
    return result

async def delete(db, campaign_id: int):
    # validate_input
    # fetch
    campaign = await campaign_repo.get(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    # persist
    await campaign_repo.delete(db, campaign)

    # return
