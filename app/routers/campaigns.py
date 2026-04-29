from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema import (
    CampaignRead,
    CampaignCreate,
    PaginatedResponse,
    PaginatedFilter,
    CampaignUpdate,
)
from app.schema.error import ErrorResponse

from app.services import campaign as campaign_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

_404 = {404: {"model": ErrorResponse}}

@router.post("/", response_model=CampaignRead, status_code=201)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    return await campaign_service.create(db, data)

@router.get("/", response_model=PaginatedResponse[CampaignRead], status_code=200)
async def list_campaigns(pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db)):
    return await campaign_service.list_campaigns(db, pagination)

@router.get("/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    return await campaign_service.get(db, campaign_id)

@router.patch("/{campaign_id}", response_model=CampaignRead, status_code=200, responses=_404)
async def update_campaign(campaign_id: int, data: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    return await campaign_service.update(db, campaign_id, data)

@router.delete("/{campaign_id}", status_code=204, responses=_404)
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    await campaign_service.delete(db, campaign_id)