from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema.demo_seed import SeedDemoDataRequest, SeedDemoDataResponse
from app.schema.error import ErrorResponse
from app.services import demo_seed as demo_seed_service

router = APIRouter(tags=["demo-seed"])

_404 = {404: {"model": ErrorResponse}}


@router.post("/clients/{client_id}/seed-demo-data", response_model=SeedDemoDataResponse, status_code=200, responses=_404)
async def seed_demo_data(client_id: int, data: SeedDemoDataRequest = SeedDemoDataRequest(), db: AsyncSession = Depends(get_db)):
    return await demo_seed_service.seed_demo_data(db, client_id, data)