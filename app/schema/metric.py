from pydantic import BaseModel

class MetricCreate(BaseModel):
    """Request body for POST /campaigns/{id}/metrics. All fields required."""
    impressions: int
    clicks: int
    spend: float


class MetricUpdate(BaseModel):
    """Request body for PATCH /metrics/{id}. All fields optional — only send what changed."""
    impressions: int | None = None
    clicks: int | None = None
    spend: float | None = None


class MetricRead(MetricCreate):
    """Response body for any endpoint returning a single metric. Deserializes from ORM via from_attributes."""
    id: int
    campaign_id: int
    model_config = {"from_attributes": True}
