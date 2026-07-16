from pydantic import BaseModel, Field


class SeedDemoDataRequest(BaseModel):
    """
    Toy/demo-only: generates synthetic historic campaigns and metrics for a client.
    The lookback window is split into exclusive day-range bands (7/30/60/90/180, capped
    at lookback_days) matching the UI's filter pills. Each band is checked independently;
    a band with zero existing metrics gets topped up with its share of datapoint_count,
    proportioned by the same recency weights used to distribute the total. Never used for
    real (non-demo) clients.
    """
    campaign_count: int = Field(3, ge=1, le=20)
    datapoint_count: int = Field(20, ge=1, le=500)
    lookback_days: int = Field(180, ge=1, le=365)
    min_spend: float = Field(10.0, ge=0)
    max_spend: float = Field(500.0, ge=0)
    min_impressions: int = Field(500, ge=0)
    max_impressions: int = Field(50_000, ge=0)
    max_ctr: float = Field(0.05, gt=0, le=1)


class SeedDemoDataResponse(BaseModel):
    seeded: bool
    campaigns_created: int
    metrics_created: int
    ranges_filled: list[int]