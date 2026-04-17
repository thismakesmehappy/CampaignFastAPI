from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://placeholder/placeholder")
ECHO_DB = os.getenv("ECHO_DB", "false").lower() == "true"

engine = create_async_engine(DATABASE_URL, echo=ECHO_DB)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Yield a database session from the connection pool. Used as a FastAPI dependency."""
    async with SessionLocal() as session:
        yield session