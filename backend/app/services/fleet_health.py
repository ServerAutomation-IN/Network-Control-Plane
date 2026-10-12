"""Fleet Host Health Monitoring Service — Network Control Plane

Periodic worker service evaluating reachability status across all registered infrastructure hosts.
Transits host status between HEALTHY/ONLINE and UNREACHABLE based on last_seen timestamps and ping probes.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.services.audit import AuditService
from app.docker.adapter import DockerAdapter


class FleetHealthWorker:
    """Service tracking health reachability status across managed hosts."""

    def __init__(self, db: AsyncSession, timeout_seconds: int = 45):
        self.db = db
        self.timeout_seconds = timeout_seconds

    async def evaluate_fleet_health(self) -> Dict[str, Any]:
        """Inspect all registered hosts and update reachability status."""
        stmt = select(InfrastructureHost)
        result = await self.db.execute(stmt)
        hosts: List[InfrastructureHost] = result.scalars().all()

        now = datetime.now(timezone.utc)
        threshold_time = now - timedelta(seconds=self.timeout_seconds)

        healthy_count = 0
        unreachable_count = 0
        status_changes = []

        for host in hosts:
            previous_status = host.status
            is_stale = host.last_seen < threshold_time

            # If host endpoint is socket/HTTP, attempt quick probe ping if stale
            is_reachable = not is_stale
            if is_stale and host.endpoint.startswith(("unix://", "http://", "https://", "tcp://")):
                try:
                    adapter = DockerAdapter(base_url=host.endpoint)
                    if await adapter.ping():
                        is_reachable = True
                        host.last_seen = now
                except Exception:
                    is_reachable = False

            new_status = "HEALTHY" if is_reachable else "UNREACHABLE"

            if previous_status != new_status:
                host.status = new_status
                status_changes.append({
                    "host_id": host.id,
                    "previous_status": previous_status,
                    "new_status": new_status,
                })
                
                await AuditService(self.db).log_event(
                    action="HOST_STATUS_CHANGE",
                    resource_type="host",
                    resource_id=host.id,
                    risk_level="MEDIUM" if new_status == "UNREACHABLE" else "LOW",
                    details={
                        "previous_status": previous_status,
                        "new_status": new_status,
                        "endpoint": host.endpoint,
                    },
                )

            if new_status in ("HEALTHY", "ONLINE"):
                healthy_count += 1
            else:
                unreachable_count += 1

        await self.db.commit()

        return {
            "total_hosts": len(hosts),
            "healthy_hosts": healthy_count,
            "unreachable_hosts": unreachable_count,
            "status_changes": status_changes,
            "evaluated_at": now.isoformat(),
        }
