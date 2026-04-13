from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL")
ECHO_DB = os.getenv("ECHO_DB")

engine = create_async_engine(DATABASE_URL, echo=ECHO_DB)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with SessionLocal() as session:
        yield session