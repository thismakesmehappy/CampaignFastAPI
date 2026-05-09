from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema import PaginatedResponse, PaginatedFilter
from app.schema.client import ClientCreate, ClientRead, ClientUpdate, ClientFilter
from app.schema.error import ErrorResponse
from app.services import client as client_service

router = APIRouter(prefix="/clients", tags=["clients"])

_404 = {404: {"model": ErrorResponse}}


@router.post("/", response_model=ClientRead, status_code=201)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db)):
    return await client_service.create(db, data)


@router.get("/", response_model=PaginatedResponse[ClientRead], status_code=200)
async def list_clients(pagination: PaginatedFilter = Depends(), options: ClientFilter = Depends(), db: AsyncSession = Depends(get_db)):
    return await client_service.list_clients(db, pagination, options)


@router.get("/{client_id}", response_model=ClientRead, status_code=200, responses=_404)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    return await client_service.get(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead, status_code=200, responses=_404)
async def update_client(client_id: int, data: ClientUpdate, db: AsyncSession = Depends(get_db)):
    return await client_service.update(db, client_id, data)


@router.delete("/{client_id}", status_code=204, responses=_404)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db)):
    await client_service.delete(db, client_id)