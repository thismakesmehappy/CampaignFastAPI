from datetime import datetime
from typing import Any

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
    created_at: datetime
    model_config = {"from_attributes": True}

class MetricSummary(MetricBase):
    total_metrics: int = Field(..., ge=0)
    campaign_id: int | None = Field(None)

class MetricFilter(BaseModel):
    campaign_name_filter: str = ""
    client_name_filter: str = ""
    ids: str = ""
    period_start: AwareDatetime | None  = None
    period_end: AwareDatetime | None = None
    min_spend: float | None = None
    max_spend: float | None = None
    min_clicks: int | None = None
    max_clicks: int | None = None
    min_impressions: int | None = None
    max_impressions: int | None = None
    sort_by: str = ""
    desc: str | None = None

    @property
    def id_list(self) -> list[int]:
        return [int(i) for i in self.ids.split(",") if i.strip()] if self.ids else []

    @property
    def sort_by_list(self) -> list[int] | list[Any]:
        return [i.strip() for i in self.sort_by.split(",")] if self.sort_by else []
