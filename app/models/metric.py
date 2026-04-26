from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.campaign import Campaign

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base

from datetime import datetime

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    impressions: Mapped[int]
    clicks: Mapped[int]
    spend: Mapped[float] = mapped_column(Float)
    campaign: Mapped["Campaign"] = relationship(back_populates="metrics")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    @validates("campaign_id")
    def validate_campaign_id(self, key, value: int) -> int:
        if value is None or value <= 0:
            raise ValueError("Campaign id must be a positive integer")
        return value

    @validates("impressions")
    def validate_impressions(self, key, value: int) -> int:
        if value is None or value < 0:
            raise ValueError("Impressions must be a non-negative integer")
        return value

    @validates("clicks")
    def validate_clicks(self, key, value: int) -> int:
        if value is None or value < 0:
            raise ValueError("Clicks must be a non-negative integer")
        return value

    @validates("spend")
    def validate_spend(self, key, value: int) -> float:
        if value is None or value < 0:
            raise ValueError("Spend must be a non-negative float")
        return value
