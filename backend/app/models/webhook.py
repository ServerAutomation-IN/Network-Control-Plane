"""Webhook Subscriptions Database Entity — Network Control Plane"""

from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WebhookSubscription(Base):
    """Represents an outbound webhook channel subscription for alert notifications."""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), default="generic", nullable=False)  # slack, pagerduty, msteams, generic
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret_token: Mapped[str] = mapped_column(String(256), nullable=False)
    subscribed_events: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
