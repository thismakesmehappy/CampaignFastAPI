from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema import (
    CampaignRead,
    PaginatedResponse,
    PaginatedFilter,
    CampaignUpdate,
)
from app.schema.error import ErrorResponse
from app.schema.campaign import CampaignFilter, CampaignCreate

from app.services import campaign as campaign_service

router = APIRouter(tags=["campaigns"])

_404 = {404: {"model": ErrorResponse}}

@router.post("/clients/{client_id}/campaigns", response_model=CampaignRead, status_code=201)
async def create_campaign(client_id: int, data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    return await campaign_service.create(db, data, client_id)

@router.get("/campaigns", response_model=PaginatedResponse[CampaignRead], status_code=200)
async def list_campaigns(pagination: PaginatedFilter = Depends(), options: CampaignFilter = Depends(), db: AsyncSession = Depends(get_db)):
    return await campaign_service.list_campaigns(db, pagination, options)

@router.get("/clients/{client_id}/campaigns", response_model=PaginatedResponse[CampaignRead], status_code=200)
async def list_campaigns_for_client(client_id: int, pagination: PaginatedFilter = Depends(), options: CampaignFilter = Depends(), db: AsyncSession = Depends(get_db)):
    return await campaign_service.list_campaigns(db, pagination, options, client_id)

@router.get("/campaigns/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    return await campaign_service.get(db, campaign_id)

@router.patch("/campaigns/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def update_campaign(campaign_id: int, data: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    return await campaign_service.update(db, campaign_id, data)

@router.delete("/campaigns/{campaign_id}", status_code=204, responses=_404)
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    await campaign_service.delete(db, campaign_id)