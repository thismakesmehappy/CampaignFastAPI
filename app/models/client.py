from __future__ import annotations
from datetime import datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.campaign import Campaign

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from app.constants import CAMPAIGN_NAME_MAX_LENGTH
from app.models.base import Base


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(CAMPAIGN_NAME_MAX_LENGTH))
    api_key: Mapped[str] = mapped_column(String())
    email: Mapped[str | None] = mapped_column(String(), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="client", cascade="all, delete-orphan")

    @validates("name")
    def validate_name(self, key, value: str) -> str:
        if value is None or len(value) > CAMPAIGN_NAME_MAX_LENGTH:
            raise ValueError(f"Name must be {CAMPAIGN_NAME_MAX_LENGTH} characters or less")
        return value

    @validates("email")
    def validate_email(self, key, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Invalid email address")
        return value