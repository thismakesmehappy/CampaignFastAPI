import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.routers import campaigns, metrics
from app.middleware import log_requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("STARTUP")
    yield
    logger.info("SHUTDOWN")

app = FastAPI(
    title="Campaign Tracker API",
    description="API for managing advertising campaigns and their performance metrics.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(campaigns.router)
app.include_router(metrics.router)

app.middleware("http")(log_requests)

register_error_handlers(app)