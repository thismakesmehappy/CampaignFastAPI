import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions import NotFoundError, DomainValidationError, ConflictError

logger = logging.getLogger(__name__)

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc):
        logger.warning("Not found: %s", exc.messages)
        return JSONResponse(status_code=404, content={"errors": exc.messages})

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request, exc: ValidationError):
        logger.warning("Query/dependency validation error: %s", exc.errors())
        return JSONResponse(status_code=422, content={"errors": [e["msg"] for e in exc.errors()]})

    @app.exception_handler(DomainValidationError)
    async def validation_handler(request, exc):
        logger.error("Validation error: %s", exc.messages)
        return JSONResponse(status_code=422, content={"errors": exc.messages})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):
        logger.warning("Conflict error: %s", exc.messages)
        return JSONResponse(status_code=409, content={"errors": exc.messages})
