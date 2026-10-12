"""InfrastructureHost Database Entity — Network Control Plane"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.network import Network
    from app.models.container import Container


class InfrastructureHost(Base):
    """Represents a managed provider host node running a workload engine."""

    __tablename__ = "infrastructure_hosts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(256), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(32), default="docker", nullable=False)
    environment: Mapped[str] = mapped_column(String(32), default="development", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    encrypted_tls_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    docker_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os: Mapped[str | None] = mapped_column(String(64), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    networks: Mapped[List["Network"]] = relationship("Network", back_populates="host", cascade="all, delete-orphan")
    containers: Mapped[List["Container"]] = relationship("Container", back_populates="host", cascade="all, delete-orphan")

    @property
    def has_tls_cert(self) -> bool:
        """Returns True if the host has an encrypted TLS certificate stored."""
        return bool(self.encrypted_tls_cert)
