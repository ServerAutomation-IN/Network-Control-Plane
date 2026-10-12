"""NetworkPolicy & PolicyResult Database Entities — Network Control Plane"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.network import Network
    from app.models.host import InfrastructureHost


class NetworkPolicy(Base):
    """Represents a declarative policy specification governing network infrastructure."""

    __tablename__ = "network_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    rules: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
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

    results: Mapped[List["PolicyResult"]] = relationship("PolicyResult", back_populates="policy", cascade="all, delete-orphan")


class PolicyResult(Base):
    """Represents compliance evaluation outcome for a specific network against a policy."""

    __tablename__ = "policy_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(64), ForeignKey("network_policies.id", ondelete="CASCADE"), nullable=False)
    network_id: Mapped[str] = mapped_column(String(64), ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    host_id: Mapped[str] = mapped_column(String(64), ForeignKey("infrastructure_hosts.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # COMPLIANT, NON_COMPLIANT
    violations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    policy: Mapped["NetworkPolicy"] = relationship("NetworkPolicy", back_populates="results")
    network: Mapped["Network"] = relationship("Network")
    host: Mapped["InfrastructureHost"] = relationship("InfrastructureHost")
