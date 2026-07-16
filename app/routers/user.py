from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema import PaginatedResponse, PaginatedFilter
from app.schema.user import UserCreate, UserRead, UserUpdate, UserFilter, LoginRequest, LoginResponse
from app.schema.error import ErrorResponse
from app.services import user as user_service

router = APIRouter(tags=["users"])

_404 = {404: {"model": ErrorResponse}}
_422 = {422: {"model": ErrorResponse}}


@router.post("/auth/login", response_model=LoginResponse, status_code=200, responses=_422)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await user_service.login(db, data)


@router.post("/users", response_model=UserRead, status_code=201, responses=_404)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await user_service.create(db, data)


@router.get("/users", response_model=PaginatedResponse[UserRead], status_code=200)
async def list_users(pagination: PaginatedFilter = Depends(), options: UserFilter = Depends(), db: AsyncSession = Depends(get_db)):
    return await user_service.list_users(db, pagination, options)


@router.get("/users/{user_id}", response_model=UserRead, status_code=200, responses=_404)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await user_service.get(db, user_id)


@router.patch("/users/{user_id}", response_model=UserRead, status_code=200, responses=_404)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    return await user_service.update(db, user_id, data)


@router.delete("/users/{user_id}", status_code=204, responses=_404)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await user_service.delete(db, user_id)