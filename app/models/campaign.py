from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.metric import Metric

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import CAMPAIGN_NAME_MAX_LENGTH, CAMPAIGN_CLIENT_MAX_LENGTH
from app.models.base import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(CAMPAIGN_NAME_MAX_LENGTH))
    client: Mapped[str] = mapped_column(String(CAMPAIGN_CLIENT_MAX_LENGTH))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    metrics: Mapped[list["Metric"]] = relationship(back_populates="campaign")
