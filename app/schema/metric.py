from pydantic import AwareDatetime, BaseModel, Field, model_validator


class MetricBase(BaseModel):
    """Basic data for metric endpoints"""
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    spend: float = Field(..., ge=0)

class MetricCreate(MetricBase):
    period_start: AwareDatetime
    period_end: AwareDatetime

    @model_validator(mode="after")
    def validate_period_star_before_end(self) -> "MetricCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be >= period_start")
        return self


class MetricUpdate(BaseModel):
    """Request body for PATCH /metrics/{id}. All fields optional — only send what changed."""
    impressions: int | None = Field(None, ge=0)
    clicks: int | None = Field(None, ge=0)
    spend: float | None = Field(None, ge=0)
    period_start: AwareDatetime | None = Field(None)
    period_end: AwareDatetime | None = Field(None)


class MetricRead(MetricCreate):
    """Response body for any endpoint returning a single metric. Deserializes from ORM via from_attributes."""
    id: int
    campaign_id: int
    model_config = {"from_attributes": True}

class MetricSummary(MetricBase):
    total_metrics: int = Field(..., ge=0)
    campaign_id: int | None = Field(None)