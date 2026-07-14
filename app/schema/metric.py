from datetime import datetime
from typing import Any

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator

from app.models.metric import MetricSource


class MetricBase(BaseModel):
    """Basic data for metric endpoints"""
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    spend: float = Field(..., ge=0)
    model_config = {"from_attributes": True}

class MetricCreate(MetricBase):
    period_start: AwareDatetime
    period_end: AwareDatetime
    source: MetricSource = MetricSource.user

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
    source: MetricSource = MetricSource.user
    model_config = {"from_attributes": True}

class MetricSummary(MetricBase):
    total_metrics: int = Field(..., ge=0)
    sources: list[MetricSource]

class MetricSummaryWithId(MetricSummary):
    id: int = Field(..., ge=0)

class MetricSummaryFilter(BaseModel):
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
    source: str = ""

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        tokens = [s.strip() for s in value.split(",") if s.strip()]
        invalid = [t for t in tokens if t != "all" and t not in MetricSource._value2member_map_]
        if invalid:
            raise ValueError(f"Invalid source(s): {', '.join(invalid)}. Must be 'all' or one of {[s.value for s in MetricSource]}")
        return value

    @property
    def sort_by_list(self) -> list[int] | list[Any]:
        return [i.strip() for i in self.sort_by.split(",")] if self.sort_by else []

    @property
    def source_list(self) -> list[MetricSource]:
        tokens = [s.strip() for s in self.source.split(",") if s.strip()]
        if not tokens or "all" in tokens:
            return list(MetricSource)
        return [MetricSource(t) for t in tokens]

class MetricSummaryList(BaseModel):
    resource_type: str = ""
    summaries: list[MetricSummaryWithId]


class MetricFilter(MetricSummaryFilter):
    campaign_name_filter: str = ""
    client_name_filter: str = ""
    ids: str = ""

    @property
    def id_list(self) -> list[int]:
        return [int(i) for i in self.ids.split(",") if i.strip()] if self.ids else []