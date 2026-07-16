from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    client_ids: list[int] = Field(..., min_length=1, max_length=1)

    @field_validator("client_ids")
    @classmethod
    def validate_single_client(cls, value: list[int]) -> list[int]:
        # client_ids is array-shaped for a future many-to-many move, but only one client
        # is supported per user today — see app/models/user.py.
        if len(value) != 1:
            raise ValueError("A user must be associated with exactly one client")
        return value


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=100)
    password: str | None = Field(None, min_length=8)
    client_ids: list[int] | None = Field(None, min_length=1, max_length=1)

    @field_validator("client_ids")
    @classmethod
    def validate_single_client(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and len(value) != 1:
            raise ValueError("A user must be associated with exactly one client")
        return value


class UserRead(BaseModel):
    """Response body for any endpoint returning a user. Never includes password_hash or is_admin (not yet exposed)."""
    id: int
    username: str
    client_ids: list[int]
    created_at: datetime
    model_config = {"from_attributes": True}


class UserFilter(BaseModel):
    username_filter: str = ""
    ids: str = ""
    sort_by: str = ""
    desc: str | None = None

    @property
    def id_list(self) -> list[int]:
        return [int(i) for i in self.ids.split(",") if i.strip()] if self.ids else []

    @property
    def sort_by_list(self) -> list[int] | list[Any]:
        return [i.strip() for i in self.sort_by.split(",")] if self.sort_by else []


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginClient(BaseModel):
    client_id: int
    client_name: str


class LoginResponse(BaseModel):
    """
    clients is a list so the wire format never needs to change when a user can belong to
    multiple clients — today it always has exactly one entry. The Angular app takes
    clients[0]; a future multi-client login adds a client-picker UI, not a new response shape.
    """
    clients: list[LoginClient]
