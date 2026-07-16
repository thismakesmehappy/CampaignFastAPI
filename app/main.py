import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from app.auth import require_api_key

from app.database import engine
from app.models import Base
from app.error_handlers import register_error_handlers
from app.routers import campaigns, metrics, clients, user
from app.middleware import log_requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("STARTUP")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("SHUTDOWN")

app = FastAPI(
    title="Campaign Tracker API",
    description="API for managing advertising campaigns and their performance metrics.",
    version="0.1.0",
    lifespan=lifespan,
    servers=[
        {"url": "http://campaignfastapi.onrender.com/", "description": "Production server"},
        {"url": "http://localhost:8000", "description": "Local dev"}
    ]
)

app.include_router(campaigns.router, dependencies=[Depends(require_api_key)])
app.include_router(metrics.router, dependencies=[Depends(require_api_key)])
app.include_router(clients.router, dependencies=[Depends(require_api_key)])
app.include_router(user.router, dependencies=[Depends(require_api_key)])

app.middleware("http")(log_requests)

register_error_handlers(app)