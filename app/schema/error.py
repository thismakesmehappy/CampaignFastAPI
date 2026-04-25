from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Response body for all error responses. Referenced in route responses={4xx: {"model": ErrorResponse}}."""
    errors: list[str]