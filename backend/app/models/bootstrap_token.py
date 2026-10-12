"""BootstrapToken Database Model — Network Control Plane"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BootstrapToken(Base):
    """Represents an ephemeral one-time token used to bootstrap and enroll edge host agents."""

    __tablename__ = "bootstrap_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. ncp_boot_<uuid>
    created_by: Mapped[str] = mapped_column(String(128), default="admin", nullable=False)
    host_name_hint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_host_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
