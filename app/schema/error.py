from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """Response body for all error responses. Referenced in route responses={4xx: {"model": ErrorResponse}}."""
    status_code: int
    error_code: str
    message: str
