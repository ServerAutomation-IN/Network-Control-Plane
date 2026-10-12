"""AI Assistant Service & Diagnostic State Machine — Network Control Plane

Handles natural language querying, service reachability diagnostics, and HITL remediation proposals.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.models.container import Container, ContainerNetwork
from app.models.network import Network
from app.models.host import InfrastructureHost
from app.models.ai import AIProposalJob
from app.schemas.ai import (
    AIQueryRequest,
    AIQueryResponse,
    AIActionProposal,
)
from app.schemas.network import ContainerAttachRequest
from app.services.inventory import InventoryService
from app.services.audit import AuditService
from app.services.ipam import IPAMService


class AIAssistantService:
    """Governed AI Agentic Assistant for natural language querying and reachability diagnostics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_query(self, request: AIQueryRequest, actor: str = "system") -> AIQueryResponse:
        """Process user NL prompt or diagnostic request."""
        provider = get_llm_provider(request.provider)
        prompt_lower = request.prompt.lower()

        # 1. Service Reachability Diagnostic Workflow
        if request.source_container or request.target_container or "reachability" in prompt_lower or "reach" in prompt_lower or "connect" in prompt_lower:
            return await self.diagnose_reachability(request, provider, actor)

        # 2. Natural Language Query Workflow
        return await self.execute_nl_query(request, provider, actor)

    async def diagnose_reachability(
        self, request: AIQueryRequest, provider: Any, actor: str
    ) -> AIQueryResponse:
        """Evaluate network path connectivity graph between source and target workload containers."""
        containers_stmt = select(Container).options(
            selectinload(Container.network_attachments).selectinload(ContainerNetwork.network)
        )
        all_containers = (await self.db.execute(containers_stmt)).scalars().all()

        source_cnt = None
        target_cnt = None

        if request.source_container:
            source_cnt = next((c for c in all_containers if c.id == request.source_container or c.name == request.source_container), None)
        if request.target_container:
            target_cnt = next((c for c in all_containers if c.id == request.target_container or c.name == request.target_container), None)

        if not source_cnt and len(all_containers) > 0:
            source_cnt = all_containers[0]
        if not target_cnt and len(all_containers) > 1:
            target_cnt = all_containers[1]

        if not source_cnt or not target_cnt:
            reasoning = await provider.generate_completion(
                prompt=f"Diagnose reachability: {request.prompt}",
                system_prompt="You are a Network Control Plane diagnostic assistant.",
            )
            return AIQueryResponse(
                provider_used=provider.get_provider_name(),
                prompt=request.prompt,
                reasoning=reasoning,
                reachability_status="UNREACHABLE",
                proposed_actions=[],
            )

        # Find shared networks
        source_net_ids = {att.network_id for att in source_cnt.network_attachments}
        target_net_ids = {att.network_id for att in target_cnt.network_attachments}
        shared_net_ids = source_net_ids.intersection(target_net_ids)

        proposed_actions: List[AIActionProposal] = []
        proposal_job_id: Optional[str] = None

        if shared_net_ids:
            shared_nets = [att.network.name for att in source_cnt.network_attachments if att.network_id in shared_net_ids]
            status_val = "REACHABLE"
            reasoning = (
                f"Workload container '{source_cnt.name}' CAN communicate with '{target_cnt.name}'. "
                f"Both endpoints are attached to shared network(s): {', '.join(shared_nets)}."
            )
        else:
            status_val = "UNREACHABLE"
            # Find a target network to attach source container to
            target_net = source_cnt.network_attachments[0].network if source_cnt.network_attachments else None
            net_name = target_net.name if target_net else "shared_overlay_bridge"
            net_id = target_net.id if target_net else "net-default"

            reasoning = (
                f"Reachability Isolation Failure: Container '{source_cnt.name}' (Host: {source_cnt.host_id}) "
                f"cannot communicate with '{target_cnt.name}' (Host: {target_cnt.host_id}). "
                f"They reside on separate network interfaces with no shared bridge or overlay network."
            )

            # Generate proposed deterministic remediation action
            action_prop = AIActionProposal(
                id=f"act-{uuid.uuid4().hex[:8]}",
                action_type="ATTACH_CONTAINER",
                target_resource=target_cnt.name,
                host_id=target_cnt.host_id,
                parameters={
                    "network_id": net_id,
                    "network_name": net_name,
                    "container_id": target_cnt.id,
                    "container_name": target_cnt.name,
                },
                risk_level="LOW",
                reason=f"Attach container '{target_cnt.name}' to network '{net_name}' to establish inter-container connectivity.",
            )
            proposed_actions.append(action_prop)

            # Persist proposal into AIProposalJob for HITL Approval Gate
            now = datetime.now(timezone.utc)
            job = AIProposalJob(
                id=f"aipol-{uuid.uuid4().hex[:12]}",
                user_prompt=request.prompt,
                diagnostic_type="reachability",
                reasoning_summary=reasoning,
                proposed_actions=[action_prop.model_dump()],
                status="PENDING_APPROVAL",
                created_at=now,
            )
            self.db.add(job)
            await self.db.commit()
            proposal_job_id = job.id

        await AuditService(self.db).log_event(
            action="AI_REACHABILITY_DIAGNOSTIC",
            resource_type="container",
            resource_id=f"{source_cnt.name}->{target_cnt.name}",
            actor=actor,
            risk_level="LOW",
            details={
                "source": source_cnt.name,
                "target": target_cnt.name,
                "status": status_val,
                "proposal_id": proposal_job_id,
            },
        )

        return AIQueryResponse(
            provider_used=provider.get_provider_name(),
            prompt=request.prompt,
            reasoning=reasoning,
            reachability_status=status_val,
            proposal_id=proposal_job_id,
            proposed_actions=proposed_actions,
        )

    async def execute_nl_query(
        self, request: AIQueryRequest, provider: Any, actor: str
    ) -> AIQueryResponse:
        """Process structured Natural Language Query over inventory & IPAM data."""
        hosts = (await self.db.execute(select(InfrastructureHost))).scalars().all()
        networks = (await self.db.execute(select(Network).options(selectinload(Network.subnets)))).scalars().all()

        ipam_service = IPAMService(self.db)
        subnets_summary = await ipam_service.get_all_subnets_summary()
        ipam_conflicts = await ipam_service.detect_conflicts()

        summary_data = {
            "total_hosts": len(hosts),
            "total_networks": len(networks),
            "total_subnets": len(subnets_summary),
            "ipam_conflicts_count": len(ipam_conflicts),
            "ipam_conflicts": [c.model_dump() for c in ipam_conflicts],
            "hosts": [{"id": h.id, "name": h.name, "status": h.status} for h in hosts],
            "networks": [
                {
                    "id": n.id,
                    "name": n.name,
                    "driver": n.driver,
                    "host_id": n.host_id,
                    "subnets": [{"subnet": s.subnet, "gateway": s.gateway} for s in n.subnets if s.subnet],
                }
                for n in networks
            ],
            "subnets": [
                {
                    "network_id": sub.network_id,
                    "network_name": sub.network_name,
                    "subnet": sub.subnet,
                    "gateway": sub.gateway,
                    "total_ips": sub.total_ips,
                    "usable_ips": sub.usable_ips,
                    "allocated_ips": sub.allocated_ips,
                    "utilization_percentage": sub.utilization_percentage,
                }
                for sub in subnets_summary
            ],
        }

        system_instructions = (
            "You are the Network Control Plane AI assistant. "
            "Provide complete, concise, and structured network/subnet summaries using bullet points. "
            f"Current Inventory & IPAM Context: {summary_data}"
        )
        reasoning = await provider.generate_completion(
            prompt=request.prompt,
            system_prompt=system_instructions,
        )

        if not reasoning or not reasoning.strip():
            subnets_str = ", ".join([f"'{s.subnet}' ({s.network_name})" for s in subnets_summary if s.subnet]) or "None"
            conflicts_str = f"Found {len(ipam_conflicts)} conflict(s)" if ipam_conflicts else "No IP subnet overlaps detected."
            reasoning = (
                f"IPAM & Network Context Summary:\n"
                f"• Total Networks: {len(networks)}\n"
                f"• Total Subnets: {len(subnets_summary)}\n"
                f"• Subnets List: {subnets_str}\n"
                f"• Overlap Status: {conflicts_str}"
            )

        await AuditService(self.db).log_event(
            action="AI_NATURAL_LANGUAGE_QUERY",
            resource_type="inventory",
            resource_id="all",
            actor=actor,
            risk_level="LOW",
            details={"prompt": request.prompt, "provider": provider.get_provider_name()},
        )

        return AIQueryResponse(
            provider_used=provider.get_provider_name(),
            prompt=request.prompt,
            reasoning=reasoning,
            query_results=summary_data,
            proposed_actions=[],
        )

    async def execute_approved_proposal(self, proposal: AIProposalJob, actor: str) -> Dict[str, Any]:
        """Execute human-approved AI remediation proposal deterministically."""
        if proposal.status != "APPROVED":
            raise ValueError(f"Proposal '{proposal.id}' cannot be executed. Current status: '{proposal.status}' (requires 'APPROVED').")

        inventory_service = InventoryService(self.db)
        results = []

        for act in proposal.proposed_actions:
            action_type = act.get("action_type")
            params = act.get("parameters", {})

            try:
                if action_type == "ATTACH_CONTAINER":
                    req = ContainerAttachRequest(container_id=params.get("container_id"))
                    att = await inventory_service.attach_container(network_id=params.get("network_id"), payload=req)
                    results.append({"action": action_type, "target": params.get("container_name"), "status": "SUCCESS", "id": att.id})
                else:
                    results.append({"action": action_type, "status": "SKIPPED", "reason": "Action type unsupported"})
            except Exception as exc:
                results.append({"action": action_type, "target": params.get("container_name"), "status": "FAILED", "error": str(exc)})

        proposal.status = "EXECUTED"
        proposal.executed_at = datetime.now(timezone.utc)
        proposal.execution_result = {"executed_by": actor, "summary": results}
        await self.db.commit()

        await AuditService(self.db).log_event(
            action="EXECUTE_AI_REMEDIATION_PROPOSAL",
            resource_type="ai_proposal",
            resource_id=proposal.id,
            actor=actor,
            risk_level="HIGH",
            details={"actions_count": len(proposal.proposed_actions), "results": results},
        )

        return proposal.execution_result
