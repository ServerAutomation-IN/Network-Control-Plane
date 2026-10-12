"""Pre-Deletion Safety Analysis Engine — Network Control Plane

Evaluates network deletion risks based on attached workloads, Compose references, and system rules.
"""

from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network import Network
from app.schemas.network import NetworkDeleteSafetyResponse


class PreDeletionSafetyEngine:
    """Calculates risk levels and safety impact prior to network deletion."""

    SYSTEM_NETWORKS = {"bridge", "host", "none"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_network_deletion(self, network_id: str) -> NetworkDeleteSafetyResponse:
        """Analyze risk of deleting a specific network entity."""
        stmt = select(Network).where(Network.id == network_id).options(
            selectinload(Network.container_attachments).selectinload(Network.container_attachments.property.mapper.class_.container)
        )
        result = await self.db.execute(stmt)
        net = result.scalar_one_or_none()

        if not net:
            return NetworkDeleteSafetyResponse(
                network_id=network_id,
                network_name="Unknown",
                risk_level="CRITICAL",
                attached_containers_count=0,
                impacted_containers=[],
                compose_project=None,
                is_safe_to_delete=False,
                risk_factors=["Network resource does not exist."],
            )

        risk_factors: List[str] = []
        impacted_containers: List[Dict[str, Any]] = []
        compose_project = net.labels.get("com.docker.compose.project") if net.labels else None

        # Rule 1: System Networks protection
        if net.name in self.SYSTEM_NETWORKS:
            risk_factors.append(f"Network '{net.name}' is a core system default network.")
            return NetworkDeleteSafetyResponse(
                network_id=net.id,
                network_name=net.name,
                risk_level="CRITICAL",
                attached_containers_count=0,
                impacted_containers=[],
                compose_project=compose_project,
                is_safe_to_delete=False,
                risk_factors=risk_factors,
            )

        # Rule 2: Attached Container Workloads
        for att in net.container_attachments:
            cnt = att.container
            if cnt:
                impacted_containers.append({
                    "container_id": cnt.id,
                    "name": cnt.name,
                    "status": cnt.status,
                    "ip_address": att.ip_address,
                })

        cnt_count = len(impacted_containers)

        if cnt_count > 0:
            risk_factors.append(f"{cnt_count} active container workload(s) currently attached.")

        if compose_project:
            risk_factors.append(f"Network belongs to Docker Compose project '{compose_project}'.")

        # Determine Risk Level & Safety Flag
        if cnt_count > 0:
            risk_level = "CRITICAL" if any(c["status"] == "running" for c in impacted_containers) else "HIGH"
            is_safe = False
        elif compose_project:
            risk_level = "MEDIUM"
            is_safe = True
        else:
            risk_level = "LOW"
            is_safe = True

        return NetworkDeleteSafetyResponse(
            network_id=net.id,
            network_name=net.name,
            risk_level=risk_level,
            attached_containers_count=cnt_count,
            impacted_containers=impacted_containers,
            compose_project=compose_project,
            is_safe_to_delete=is_safe,
            risk_factors=risk_factors,
        )
