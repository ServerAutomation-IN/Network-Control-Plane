"""ReconciliationJob Database Entity — Network Control Plane"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReconciliationJob(Base):
    """Represents a desired-state reconciliation plan and approval workflow state."""

    __tablename__ = "reconciliation_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manifest_name: Mapped[str] = mapped_column(String(128), nullable=False)
    desired_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    drifts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    plan_actions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING_APPROVAL", nullable=False)  # PENDING_APPROVAL, APPROVED, EXECUTED, REJECTED
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    execution_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
