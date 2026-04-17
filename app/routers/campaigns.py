from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schema import (
    CampaignRead,
    CampaignCreate,
    PaginatedResponse,
    PaginatedFilter,
    CampaignUpdate,
)
from app.schema.error import ErrorResponse

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

_404 = {404: {"model": ErrorResponse}}

@router.post("/", response_model=CampaignRead, status_code=201)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_campaign(db, data)

@router.get("/", response_model=PaginatedResponse[CampaignRead], status_code=200)
async def list_campaigns(pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db)):
    campaigns_list = await crud.list_campaigns(db, pagination)
    total = await crud.get_total_number_of_campaigns(db)
    has_more = pagination.offset + len(campaigns_list) < total
    response = PaginatedResponse(items=campaigns_list, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)
    return response

@router.get("/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.patch("/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def update_campaign(campaign_id: int, data: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    campaign = await crud.update_campaign(db, campaign_id, data)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.delete("/{campaign_id}", status_code=204, responses=_404)
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")