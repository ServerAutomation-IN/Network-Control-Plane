"""Drift Detection & GitOps Reconciliation Engine — Network Control Plane

Parses desired-state YAML manifests, calculates runtime infrastructure drift diffs, and generates human-approved reconciliation plans.
"""

import uuid
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network import Network
from app.models.drift import ReconciliationJob
from app.schemas.drift import (
    NetworkManifestSpec,
    DesiredNetworkSpec,
    DriftDiffItem,
    DriftType,
    ReconciliationAction,
    ReconciliationStatus,
)
from app.schemas.network import NetworkCreateRequest, NetworkSubnetCreate
from app.services.inventory import InventoryService
from app.services.audit import AuditService

CORE_SYSTEM_NETWORKS = {"bridge", "host", "none", "control_plane_frontend", "control_plane_backend"}


class DriftEngine:
    """Service detecting configuration drift between desired-state YAML specs and actual runtime state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def parse_yaml_manifest(yaml_content: str) -> NetworkManifestSpec:
        """Parse raw YAML string into validated NetworkManifestSpec pydantic model."""
        try:
            raw_data = yaml.safe_load(yaml_content)
            if not isinstance(raw_data, dict):
                raise ValueError("Parsed YAML is not a valid key-value mapping.")
            api_ver = raw_data.get("apiVersion")
            if api_ver != "network-control-plane/v1":
                raise ValueError(f"Unsupported apiVersion '{api_ver}'. Expected 'network-control-plane/v1'.")
            return NetworkManifestSpec.model_validate(raw_data)
        except Exception as exc:
            raise ValueError(f"YAML Manifest Parsing Error: {exc}")

    async def compare_manifest_against_runtime(
        self, yaml_content: str
    ) -> Tuple[str, List[DriftDiffItem], List[ReconciliationAction]]:
        """Compare desired-state YAML spec against PostgreSQL runtime inventory."""
        manifest = self.parse_yaml_manifest(yaml_content)
        manifest_name = manifest.metadata.get("name", "Unnamed Manifest")
        desired_networks = manifest.spec.get("networks", [])

        # Fetch actual runtime networks
        stmt = select(Network).options(selectinload(Network.subnets), selectinload(Network.container_attachments))
        runtime_networks = (await self.db.execute(stmt)).scalars().all()

        desired_map: Dict[Tuple[str, str], DesiredNetworkSpec] = {
            (n.host_id, n.name): n for n in desired_networks
        }
        runtime_map: Dict[Tuple[str, str], Network] = {
            (net.host_id, net.name): net for net in runtime_networks
        }

        drifts: List[DriftDiffItem] = []
        actions: List[ReconciliationAction] = []

        # 1. Identify MISSING_IN_RUNTIME networks
        for (host_id, net_name), desired_net in desired_map.items():
            if (host_id, net_name) not in runtime_map:
                drifts.append(
                    DriftDiffItem(
                        resource_type="network",
                        resource_name=net_name,
                        host_id=host_id,
                        drift_type=DriftType.MISSING_IN_RUNTIME,
                        desired_value=f"driver={desired_net.driver}, internal={desired_net.internal}",
                        actual_value="ABSENT",
                        severity="HIGH",
                        details=f"Network '{net_name}' is declared in manifest but missing on host '{host_id}'.",
                    )
                )

                subnets_payload = [
                    {"subnet": s.subnet, "gateway": s.gateway, "ip_range": s.ip_range}
                    for s in desired_net.subnets
                ]

                actions.append(
                    ReconciliationAction(
                        id=f"act-{uuid.uuid4().hex[:8]}",
                        action_type="CREATE_NETWORK",
                        target_resource=net_name,
                        host_id=host_id,
                        parameters={
                            "host_id": host_id,
                            "name": net_name,
                            "driver": desired_net.driver,
                            "scope": desired_net.scope,
                            "internal": desired_net.internal,
                            "attachable": desired_net.attachable,
                            "labels": desired_net.labels,
                            "subnets": subnets_payload,
                        },
                        risk_level="LOW",
                        reason=f"Create missing desired network '{net_name}' on host '{host_id}'.",
                    )
                )

        # 2. Identify EXTRA_IN_RUNTIME unmanaged networks
        for (host_id, net_name), runtime_net in runtime_map.items():
            if net_name in CORE_SYSTEM_NETWORKS:
                continue  # Skip system default networks

            if (host_id, net_name) not in desired_map:
                containers_attached = len(runtime_net.container_attachments)
                drifts.append(
                    DriftDiffItem(
                        resource_type="network",
                        resource_name=net_name,
                        host_id=host_id,
                        drift_type=DriftType.EXTRA_IN_RUNTIME,
                        desired_value="ABSENT",
                        actual_value=f"driver={runtime_net.driver}, containers={containers_attached}",
                        severity="MEDIUM" if containers_attached == 0 else "CRITICAL",
                        details=f"Network '{net_name}' exists in runtime but is not declared in desired manifest.",
                    )
                )

                actions.append(
                    ReconciliationAction(
                        id=f"act-{uuid.uuid4().hex[:8]}",
                        action_type="DELETE_NETWORK",
                        target_resource=runtime_net.id,
                        host_id=host_id,
                        parameters={"network_id": runtime_net.id, "network_name": net_name, "force": False},
                        risk_level="HIGH" if containers_attached > 0 else "MEDIUM",
                        reason=f"Prune unmanaged drift network '{net_name}' from host '{host_id}'.",
                    )
                )

        # 3. Identify MODIFIED_CONFIG discrepancies
        for (host_id, net_name), desired_net in desired_map.items():
            if (host_id, net_name) in runtime_map:
                runtime_net = runtime_map[(host_id, net_name)]
                if runtime_net.driver != desired_net.driver:
                    drifts.append(
                        DriftDiffItem(
                            resource_type="network",
                            resource_name=net_name,
                            host_id=host_id,
                            drift_type=DriftType.MODIFIED_CONFIG,
                            property_name="driver",
                            desired_value=desired_net.driver,
                            actual_value=runtime_net.driver,
                            severity="HIGH",
                            details=f"Driver configuration drift on network '{net_name}' (desired: '{desired_net.driver}', actual: '{runtime_net.driver}').",
                        )
                    )

                if runtime_net.internal != desired_net.internal:
                    drifts.append(
                        DriftDiffItem(
                            resource_type="network",
                            resource_name=net_name,
                            host_id=host_id,
                            drift_type=DriftType.MODIFIED_CONFIG,
                            property_name="internal",
                            desired_value=desired_net.internal,
                            actual_value=runtime_net.internal,
                            severity="MEDIUM",
                            details=f"Internal routing flag drift on network '{net_name}'.",
                        )
                    )

        return manifest_name, drifts, actions

    async def execute_reconciliation_plan(
        self, job: ReconciliationJob, actor: str
    ) -> Dict[str, Any]:
        """Execute a human-approved reconciliation plan against actual provider infrastructure."""
        if job.status != ReconciliationStatus.APPROVED.value:
            raise ValueError(f"Reconciliation job '{job.id}' cannot be executed. Current status: '{job.status}' (requires 'APPROVED').")

        inventory_service = InventoryService(self.db)
        results = []

        for act_dict in job.plan_actions:
            action_type = act_dict.get("action_type")
            params = act_dict.get("parameters", {})

            try:
                if action_type == "CREATE_NETWORK":
                    subnets = [NetworkSubnetCreate(**s) for s in params.get("subnets", [])]
                    req = NetworkCreateRequest(
                        host_id=params.get("host_id", "host-local-docker-host"),
                        name=params.get("name"),
                        driver=params.get("driver", "bridge"),
                        scope=params.get("scope", "local"),
                        internal=params.get("internal", False),
                        attachable=params.get("attachable", False),
                        labels=params.get("labels", {}),
                        subnets=subnets,
                    )
                    created_net = await inventory_service.create_network(req)
                    results.append({"action": action_type, "resource": params.get("name"), "status": "SUCCESS", "id": created_net.id})

                elif action_type == "DELETE_NETWORK":
                    net_id = params.get("network_id")
                    await inventory_service.delete_network(network_id=net_id, force=params.get("force", False))
                    results.append({"action": action_type, "resource": params.get("network_name"), "status": "SUCCESS", "id": net_id})

            except Exception as exc:
                results.append({"action": action_type, "resource": params.get("name") or params.get("network_name"), "status": "FAILED", "error": str(exc)})

        job.status = ReconciliationStatus.EXECUTED.value
        job.executed_at = datetime.now(timezone.utc)
        job.execution_result = {"executed_by": actor, "summary": results}
        await self.db.commit()

        await AuditService(self.db).log_event(
            action="EXECUTE_RECONCILIATION_PLAN",
            resource_type="reconciliation_job",
            resource_id=job.id,
            actor=actor,
            risk_level="HIGH",
            details={"actions_count": len(job.plan_actions), "results": results},
        )

        return job.execution_result
