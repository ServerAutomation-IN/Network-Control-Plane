"""AuditEvent Database Entity — Network Control Plane"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditEvent(Base):
    """Represents an immutable security and audit log record for network state mutations."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # CREATE_NETWORK, DELETE_NETWORK, ATTACH_CONTAINER, DETACH_CONTAINER, PRUNE_NETWORKS
    actor: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)  # network, container, host
    resource_id: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), default="LOW", nullable=False)  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
