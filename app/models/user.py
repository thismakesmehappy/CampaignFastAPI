from __future__ import annotations
from datetime import datetime

from sqlalchemy import String, DateTime, func, BigInteger, ARRAY, Boolean
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.models.base import Base

_USERNAME_MAX_LENGTH = 100


class User(Base):
    """
    client_ids is an array rather than a single FK so a future move to many-to-many
    doesn't require a schema migration — for now the app layer enforces exactly one entry.
    is_admin is not yet exposed via any schema/endpoint; wiring it up (scoping list/get
    endpoints to bypass client filtering for admins) is future admin-path work.
    """
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(_USERNAME_MAX_LENGTH), unique=True)
    password_hash: Mapped[str] = mapped_column(String())
    client_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @validates("username")
    def validate_username(self, key, value: str) -> str:
        if not value or len(value) > _USERNAME_MAX_LENGTH:
            raise ValueError(f"Username must be 1-{_USERNAME_MAX_LENGTH} characters")
        return value