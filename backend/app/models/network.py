"""Network & NetworkSubnet Database Entities — Network Control Plane"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.host import InfrastructureHost
    from app.models.container import ContainerNetwork


class Network(Base):
    """Represents a normalized provider network entity."""

    __tablename__ = "networks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    host_id: Mapped[str] = mapped_column(String(64), ForeignKey("infrastructure_hosts.id", ondelete="CASCADE"), nullable=False)
    provider_ref_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attachable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ingress: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    labels: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    host: Mapped["InfrastructureHost"] = relationship("InfrastructureHost", back_populates="networks")
    subnets: Mapped[List["NetworkSubnet"]] = relationship("NetworkSubnet", back_populates="network", cascade="all, delete-orphan")
    container_attachments: Mapped[List["ContainerNetwork"]] = relationship("ContainerNetwork", back_populates="network", cascade="all, delete-orphan")


class NetworkSubnet(Base):
    """Represents a subnet allocation under a network."""

    __tablename__ = "network_subnets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    network_id: Mapped[str] = mapped_column(String(64), ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    subnet: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gateway: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_range: Mapped[str | None] = mapped_column(String(64), nullable=True)

    network: Mapped["Network"] = relationship("Network", back_populates="subnets")
