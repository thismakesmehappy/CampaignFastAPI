from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schema import (
    MetricRead,
    MetricBase,
    MetricUpdate,
    PaginatedFilter,
    PaginatedResponse,
)

from app.schema.error import ErrorResponse


router = APIRouter(tags=["metrics"])

_404 = {404: {"model": ErrorResponse}}

@router.post("/campaigns/{campaign_id}/metrics/", response_model=MetricRead, status_code=201, responses=_404)
async def create_metric(campaign_id: int, data: MetricBase, db: AsyncSession = Depends(get_db)):
    campaign = await crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await crud.create_metric(db, campaign_id, data)

@router.get("/campaigns/{campaign_id}/metrics/", response_model=PaginatedResponse[MetricRead], status_code=200, responses=_404)
async def list_metrics_for_campaign(campaign_id: int, pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db)):
    campaign = await crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    metrics_list = await crud.list_metrics(db, pagination, campaign_id)
    total = await crud.get_total_number_of_metrics(db, campaign_id)
    has_more = pagination.offset + len(metrics_list) < total
    response = PaginatedResponse(
        items=metrics_list,
        has_more=has_more,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return response

@router.get("/metrics/", response_model=PaginatedResponse[MetricRead], status_code=200)
async def list_metrics(pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db)):
    metrics_list = await crud.list_metrics(db, pagination)
    total = await crud.get_total_number_of_metrics(db)
    has_more = pagination.offset + len(metrics_list) < total
    response = PaginatedResponse(items=metrics_list, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)
    return response

@router.get("/metrics/{metric_id}/", response_model=MetricRead, status_code=200, responses=_404)
async def get_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
    metric = await crud.get_metric(db, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric

@router.patch("/metrics/{metric_id}/", response_model=MetricRead, status_code=200, responses=_404)
async def update_metric(metric_id: int, data: MetricUpdate, db: AsyncSession = Depends(get_db)):
    metric = await crud.update_metric(db, metric_id, data)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric

@router.delete("/metrics/{metric_id}/", status_code=204, responses=_404)
async def delete_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_metric(db, metric_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Metric not found")
