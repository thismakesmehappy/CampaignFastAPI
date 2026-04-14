from datetime import datetime
from pydantic import BaseModel, Field

from app.constants import (
    CAMPAIGN_NAME_MIN_LENGTH, CAMPAIGN_NAME_MAX_LENGTH,
    CAMPAIGN_CLIENT_MIN_LENGTH, CAMPAIGN_CLIENT_MAX_LENGTH,
)

class CampaignCreate(BaseModel):
    """Request body for POST /campaigns. All fields required."""
    name: str = Field(..., min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)
    client: str = Field(..., min_length=CAMPAIGN_CLIENT_MIN_LENGTH, max_length=CAMPAIGN_CLIENT_MAX_LENGTH)


class CampaignUpdate(BaseModel):
    """Request body for PATCH /campaigns/{id}. All fields optional — only send what changed."""
    name: str | None = Field(None, min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)
    client: str | None = Field(None, min_length=CAMPAIGN_CLIENT_MIN_LENGTH, max_length=CAMPAIGN_CLIENT_MAX_LENGTH)


class CampaignRead(CampaignCreate):
    """Response body for any endpoint returning a single campaign. Deserializes from ORM via from_attributes."""
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

