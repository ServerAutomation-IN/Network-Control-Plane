"""Container & ContainerNetwork Database Entities — Network Control Plane"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.host import InfrastructureHost
    from app.models.network import Network


class Container(Base):
    """Represents a workload container instance running on a host."""

    __tablename__ = "containers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    host_id: Mapped[str] = mapped_column(String(64), ForeignKey("infrastructure_hosts.id", ondelete="CASCADE"), nullable=False)
    provider_ref_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    image: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    labels: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    host: Mapped["InfrastructureHost"] = relationship("InfrastructureHost", back_populates="containers")
    network_attachments: Mapped[List["ContainerNetwork"]] = relationship("ContainerNetwork", back_populates="container", cascade="all, delete-orphan")


class ContainerNetwork(Base):
    """Junction table for workload attachment to network with IP assignment."""

    __tablename__ = "container_networks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    container_id: Mapped[str] = mapped_column(String(64), ForeignKey("containers.id", ondelete="CASCADE"), nullable=False)
    network_id: Mapped[str] = mapped_column(String(64), ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ipv6_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    container: Mapped["Container"] = relationship("Container", back_populates="network_attachments")
    network: Mapped["Network"] = relationship("Network", back_populates="container_attachments")
