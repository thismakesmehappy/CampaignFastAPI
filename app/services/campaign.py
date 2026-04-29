from app.repositories import campaign as campaign_repo
from app.exceptions import NotFoundError
from app.models import Campaign
from app.schema import CampaignCreate, PaginatedFilter, PaginatedResponse, CampaignUpdate


async def create(db, data: CampaignCreate) -> Campaign:
    # validate_input
    # fetch
    # validate
    # merge
    campaign = Campaign(name=data.name, client=data.client)

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

async def list_campaigns(db, pagination: PaginatedFilter):
    # validate_input
    # fetch
    campaigns_list = await campaign_repo.find_all(db, pagination)
    total = await campaign_repo.count(db)

    # validate
    # merge
    has_more = pagination.offset + len(campaigns_list) < total
    response = PaginatedResponse(items=campaigns_list, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)

    # return
    return response

async def update(db, campaign_id: int, data: CampaignUpdate):
    # validate_input
    # fetch
    campaign = await campaign_repo.get(db, campaign_id)

    # validate
    errors = NotFoundError()
    if campaign is None:
        errors.capture("Campaign")
    errors.raise_if_any()

    # merge
    if data.name is not None:
        campaign.name = data.name
    if data.client is not None:
        campaign.client = data.client

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
