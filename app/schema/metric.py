from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    """Request body for POST /campaigns/{id}/metrics. All fields required."""
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    spend: float = Field(..., ge=0)


class MetricUpdate(BaseModel):
    """Request body for PATCH /metrics/{id}. All fields optional — only send what changed."""
    impressions: int | None = Field(None, ge=0)
    clicks: int | None = Field(None, ge=0)
    spend: float | None = Field(None, ge=0)


class MetricRead(MetricCreate):
    """Response body for any endpoint returning a single metric. Deserializes from ORM via from_attributes."""
    id: int
    campaign_id: int
    model_config = {"from_attributes": True}
