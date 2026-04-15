from pydantic import BaseModel
from typing import Generic, TypeVar

from app.constants import PAGE_LIMIT_DEFAULT, PAGE_LIMIT_MIN, PAGE_LIMIT_MAX

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Response envelope for paginated list endpoints. Use as response_model=PaginatedResponse[CampaignRead]."""
    items: list[T]
    total: int
    offset: int
    limit: int
    has_more: bool
    model_config = {"from_attributes": True}


class PaginatedFilter:
    """Pagination parameters for CRUD list functions. Instantiate directly or via a router dependency."""
    def __init__(
        self,
        limit: int = PAGE_LIMIT_DEFAULT,
        offset: int = 0,
    ):
        self.limit = limit
        self.offset = offset
