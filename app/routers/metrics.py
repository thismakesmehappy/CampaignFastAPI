from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schema import (
    MetricRead,
    MetricCreate,
    MetricUpdate,
    MetricSummary,
    PaginatedFilter,
    PaginatedResponse,
)

from app.schema.error import ErrorResponse

from app.services import metric as metric_service
from app.schema.metric import MetricFilter, MetricSummaryFilter, MetricSummaryList

router = APIRouter(tags=["metrics"])

_404 = {404: {"model": ErrorResponse}}

@router.post("/campaigns/{campaign_id}/metrics", response_model=MetricRead, status_code=201, responses=_404)
async def create_metric(campaign_id: int, data: MetricCreate, db: AsyncSession = Depends(get_db)):
    return await metric_service.create(db, campaign_id, data)

@router.get("/campaigns/metrics/summary", response_model=MetricSummaryList, status_code=200, responses=_404)
async def list_metrics_summary_for_campaigns(ids: str = Query(...), db: AsyncSession = Depends(get_db), options: MetricSummaryFilter = Depends()):
    return await metric_service.metrics_summary_for_campaigns(db, ids, options)

@router.get("/campaigns/{campaign_id}/metrics", response_model=PaginatedResponse[MetricRead], status_code=200, responses=_404)
async def list_metrics_for_campaign(campaign_id: int, pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db), options: MetricFilter = Depends()):
    return await metric_service.list_metrics(db, pagination, campaign_id, None, options)

@router.get("/clients/metrics/summary", response_model=MetricSummaryList, status_code=200, responses=_404)
async def list_metrics_summary_for_clients(ids: str = Query(...), db: AsyncSession = Depends(get_db), options: MetricSummaryFilter = Depends()):
    return await metric_service.metrics_summary_for_clients(db, ids, options)

@router.get("/clients/{client_id}/metrics", response_model=PaginatedResponse[MetricRead], status_code=200, responses=_404)
async def list_metrics_for_client(client_id: int, pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db), options: MetricFilter = Depends()):
    return await metric_service.list_metrics(db, pagination, None, client_id, options)

@router.get("/metrics/summary", response_model=MetricSummary, status_code=200)
async def list_metrics_summary(ids: str = Query(default=""), db: AsyncSession = Depends(get_db), options: MetricSummaryFilter = Depends()):
    return await metric_service.metrics_summary(db, ids=ids, options=options)

@router.get("/metrics", response_model=PaginatedResponse[MetricRead], status_code=200)
async def list_metrics(pagination: PaginatedFilter = Depends(), db: AsyncSession = Depends(get_db), options: MetricFilter = Depends()):
    return await metric_service.list_metrics(db, pagination, options=options)

@router.get("/metrics/{metric_id}", response_model=MetricRead, status_code=200, responses=_404)
async def get_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
    return await metric_service.get(db, metric_id)

@router.patch("/metrics/{metric_id}", response_model=MetricRead, status_code=200, responses={**_404, 422: {"model": ErrorResponse}})
async def update_metric(metric_id: int, data: MetricUpdate, db: AsyncSession = Depends(get_db)):
    return await metric_service.update(db, metric_id, data)

@router.delete("/metrics/{metric_id}", status_code=204, responses=_404)
async def delete_metric(metric_id: int, db: AsyncSession = Depends(get_db)):
    await metric_service.delete(db, metric_id)