import os
import re
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://placeholder/placeholder")
ECHO_DB = os.getenv("ECHO_DB", "false").lower() == "true"

_connect_args = {"ssl": "require"} if "neon.tech" in DATABASE_URL else {}
# Strip sslmode from URL — asyncpg doesn't accept it as a query param
_DB_URL = re.sub(r"[?&]sslmode=[^&]*", "", DATABASE_URL).rstrip("?")
engine = create_async_engine(_DB_URL, echo=ECHO_DB, connect_args=_connect_args)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Yield a database session from the connection pool. Used as a FastAPI dependency."""
    async with SessionLocal() as session:
        yield session