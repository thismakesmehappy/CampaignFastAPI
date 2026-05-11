from datetime import datetime
from pydantic import BaseModel, Field

from app.constants import CAMPAIGN_NAME_MIN_LENGTH, CAMPAIGN_NAME_MAX_LENGTH


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)
    email: str | None = None
    notes: str | None = None
    is_active: bool = True


class ClientUpdate(BaseModel):
    name: str | None = Field(None, min_length=CAMPAIGN_NAME_MIN_LENGTH, max_length=CAMPAIGN_NAME_MAX_LENGTH)
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClientFilter(BaseModel):
    name_filter: str = ""
    ids: str = ""

    @property
    def id_list(self) -> list[int]:
        return [int(i) for i in self.ids.split(",") if i.strip()] if self.ids else []


class ClientRead(BaseModel):
    id: int
    name: str
    api_key: str
    email: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
