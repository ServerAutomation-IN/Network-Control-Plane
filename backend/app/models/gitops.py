"""GitOpsRepository Database Entity — Network Control Plane"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GitOpsRepository(Base):
    """Represents a registered Git repository providing desired-state network manifests."""

    __tablename__ = "gitops_repositories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(256), nullable=False)
    branch: Mapped[str] = mapped_column(String(64), default="main", nullable=False)
    manifest_path: Mapped[str] = mapped_column(String(256), default="deployment/network-manifest.yaml", nullable=False)
    auth_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_interval_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)  # Default 5 minutes
    auto_reconcile_low_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync_status: Mapped[str] = mapped_column(String(32), default="SYNCED", nullable=False)  # SYNCED, OUT_OF_SYNC, SYNCING, FAILED
    last_commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
