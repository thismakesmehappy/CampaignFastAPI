from datetime import datetime
from pydantic import BaseModel, Field

from app.constants import (
    CAMPAIGN_NAME_MIN_LENGTH, CAMPAIGN_NAME_MAX_LENGTH,
)

class CampaignCreate(BaseModel):
    """Request body for POST /clients/{client_id}/campaigns. client_id comes from the path."""
    name: str = Field(..., min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)


class CampaignUpdate(BaseModel):
    """Request body for PATCH /campaigns/{id}. All fields optional — only send what changed."""
    name: str | None = Field(None, min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)
    client_id: int | None = Field(None)


class CampaignRead(CampaignCreate):
    """Response body for any endpoint returning a single campaign. Deserializes from ORM via from_attributes."""
    id: int
    client_id: int
    created_at: datetime
    model_config = {"from_attributes": True}

class CampaignFilter(BaseModel):
    name_filter: str = ""
    client_name_filter: str = ""
    ids: str = ""

    @property
    def id_list(self) -> list[int]:
        return [int(i) for i in self.ids.split(",") if i.strip()] if self.ids else []
