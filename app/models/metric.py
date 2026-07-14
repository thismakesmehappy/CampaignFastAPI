from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class MetricSource(str, enum.Enum):
    user = "user"
    system = "system"


class Metric(Base):
    __tablename__ = "metrics"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("campaigns.id"))
    impressions: Mapped[int]
    clicks: Mapped[int]
    spend: Mapped[float] = mapped_column(Float)
    campaign: Mapped["Campaign"] = relationship(back_populates="metrics")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[MetricSource] = mapped_column(Enum(MetricSource), default=MetricSource.user, nullable=False)
    
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
