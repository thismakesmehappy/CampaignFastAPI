from fastapi import FastAPI

from app.routers import campaigns, metrics

app = FastAPI(
    title="Campaign Tracker API",
    description="API for managing advertising campaigns and their performance metrics.",
    version="0.1.0",
)

app.include_router(campaigns.router)
app.include_router(metrics.router)
