"""Policy Evaluation Engine Service — Network Control Plane

Evaluates declarative policies against network infrastructure entities for compliance and pre-execution safety.
"""

import ipaddress
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.policy import NetworkPolicy, PolicyResult
from app.models.network import Network, NetworkSubnet
from app.schemas.policy import (
    PolicyRulesSpec,
    PolicySeverity,
    ComplianceStatus,
    ViolationDetail,
    ComplianceReport,
    PolicyEvaluationResultResponse,
)
from app.services.audit import AuditService


class PolicyEngine:
    """Service enforcing declarative governance policy evaluation on network entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def check_subnet_in_cidrs(subnet_str: str, approved_cidrs: List[str]) -> bool:
        """Check if target subnet IP network is contained within any of the approved CIDR ranges."""
        try:
            target_net = ipaddress.ip_network(subnet_str, strict=False)
            for approved_str in approved_cidrs:
                approved_net = ipaddress.ip_network(approved_str, strict=False)
                if target_net.subnet_of(approved_net):
                    return True
            return False
        except Exception:
            return False

    def evaluate_rules(
        self,
        driver: str,
        labels: Dict[str, str],
        subnets: List[str],
        internal: bool,
        rules_dict: Dict[str, Any],
        severity: str = "HIGH",
    ) -> List[ViolationDetail]:
        """Pure evaluation function checking network properties against rules spec."""
        violations: List[ViolationDetail] = []
        rules = PolicyRulesSpec.model_validate(rules_dict)

        # 1. Allowed drivers rule
        if rules.allowed_drivers is not None:
            allowed = [d.lower() for d in rules.allowed_drivers]
            if driver.lower() not in allowed:
                violations.append(
                    ViolationDetail(
                        rule_type="driver",
                        message=f"Network driver '{driver}' is not in allowed list: {rules.allowed_drivers}",
                        severity=PolicySeverity(severity),
                    )
                )

        # 2. Blocked drivers rule
        if rules.blocked_drivers is not None:
            blocked = [d.lower() for d in rules.blocked_drivers]
            if driver.lower() in blocked:
                violations.append(
                    ViolationDetail(
                        rule_type="driver",
                        message=f"Network driver '{driver}' is explicitly forbidden",
                        severity=PolicySeverity(severity),
                    )
                )

        # 3. Required key-value labels rule
        if rules.required_labels:
            for req_key, req_val in rules.required_labels.items():
                actual_val = labels.get(req_key) if labels else None
                if actual_val != req_val:
                    violations.append(
                        ViolationDetail(
                            rule_type="label",
                            message=f"Required label '{req_key}={req_val}' missing or mismatched (found '{actual_val}')",
                            severity=PolicySeverity(severity),
                        )
                    )

        # 4. Required label keys rule
        if rules.required_label_keys:
            for req_key in rules.required_label_keys:
                if not labels or req_key not in labels:
                    violations.append(
                        ViolationDetail(
                            rule_type="label",
                            message=f"Required label key '{req_key}' missing on network",
                            severity=PolicySeverity(severity),
                        )
                    )

        # 5. Approved CIDR ranges rule
        if rules.approved_cidr_ranges and subnets:
            for sub_str in subnets:
                if sub_str and not self.check_subnet_in_cidrs(sub_str, rules.approved_cidr_ranges):
                    violations.append(
                        ViolationDetail(
                            rule_type="cidr",
                            message=f"Subnet '{sub_str}' is outside approved CIDR ranges {rules.approved_cidr_ranges}",
                            severity=PolicySeverity(severity),
                        )
                    )

        # 6. Internal network requirement rule
        if rules.require_internal is True and not internal:
            violations.append(
                ViolationDetail(
                    rule_type="internal",
                    message="Network must be marked internal=True according to governance policy",
                    severity=PolicySeverity(severity),
                )
            )

        # 7. Max subnets rule
        if rules.max_subnets_per_network is not None:
            if len(subnets) > rules.max_subnets_per_network:
                violations.append(
                    ViolationDetail(
                        rule_type="capacity",
                        message=f"Network has {len(subnets)} subnets, exceeding maximum limit of {rules.max_subnets_per_network}",
                        severity=PolicySeverity(severity),
                    )
                )

        return violations

    async def evaluate_all(self) -> List[PolicyResult]:
        """Evaluate all active policies across all networks in inventory and persist results."""
        policies_stmt = select(NetworkPolicy).where(NetworkPolicy.enabled == True)
        policies = (await self.db.execute(policies_stmt)).scalars().all()

        networks_stmt = select(Network).options(selectinload(Network.subnets))
        networks = (await self.db.execute(networks_stmt)).scalars().all()

        now = datetime.now(timezone.utc)
        results: List[PolicyResult] = []

        # Clear existing policy results to avoid stale evaluations
        await self.db.execute(delete(PolicyResult))

        for pol in policies:
            for net in networks:
                subnet_strings = [s.subnet for s in net.subnets if s.subnet]
                violations = self.evaluate_rules(
                    driver=net.driver,
                    labels=net.labels or {},
                    subnets=subnet_strings,
                    internal=net.internal,
                    rules_dict=pol.rules,
                    severity=pol.severity,
                )

                status_val = (
                    ComplianceStatus.NON_COMPLIANT.value
                    if violations
                    else ComplianceStatus.COMPLIANT.value
                )

                result_entity = PolicyResult(
                    id=str(uuid.uuid4()),
                    policy_id=pol.id,
                    network_id=net.id,
                    host_id=net.host_id,
                    status=status_val,
                    violations=[v.model_dump() for v in violations],
                    evaluated_at=now,
                )
                self.db.add(result_entity)
                results.append(result_entity)

        await self.db.commit()

        # Log audit event
        await AuditService(self.db).log_event(
            action="POLICY_EVALUATION_ALL",
            resource_type="policy",
            resource_id="all",
            risk_level="LOW",
            details={
                "policies_count": len(policies),
                "networks_count": len(networks),
                "total_evaluations": len(results),
                "non_compliant_count": sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT.value),
            },
        )

        return results

    async def get_compliance_report(self) -> ComplianceReport:
        """Calculate and return full compliance summary report."""
        # Ensure fresh evaluations exist
        await self.evaluate_all()

        stmt = select(PolicyResult).options(selectinload(PolicyResult.policy), selectinload(PolicyResult.network))
        results = (await self.db.execute(stmt)).scalars().all()

        # Query total unique networks
        net_count_stmt = select(Network)
        all_nets = (await self.db.execute(net_count_stmt)).scalars().all()
        total_networks = len(all_nets)

        # Identify non-compliant network IDs
        non_compliant_net_ids = {
            r.network_id for r in results if r.status == ComplianceStatus.NON_COMPLIANT.value
        }
        non_compliant_count = len(non_compliant_net_ids)
        compliant_count = max(0, total_networks - non_compliant_count)
        compliance_pct = (compliant_count / total_networks * 100.0) if total_networks > 0 else 100.0

        violations_by_severity = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        report_results: List[PolicyEvaluationResultResponse] = []

        for r in results:
            pol_name = r.policy.name if r.policy else "Unknown Policy"
            pol_sev = r.policy.severity if r.policy else "HIGH"
            net_name = r.network.name if r.network else "Unknown Network"

            violations_list = [ViolationDetail.model_validate(v) for v in r.violations]
            if r.status == ComplianceStatus.NON_COMPLIANT.value:
                violations_by_severity[pol_sev] = violations_by_severity.get(pol_sev, 0) + len(violations_list)

            report_results.append(
                PolicyEvaluationResultResponse(
                    id=r.id,
                    policy_id=r.policy_id,
                    policy_name=pol_name,
                    severity=PolicySeverity(pol_sev),
                    network_id=r.network_id,
                    network_name=net_name,
                    host_id=r.host_id,
                    status=ComplianceStatus(r.status),
                    violations=violations_list,
                    evaluated_at=r.evaluated_at,
                )
            )

        return ComplianceReport(
            total_networks=total_networks,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            compliance_percentage=round(compliance_pct, 1),
            violations_by_severity=violations_by_severity,
            results=report_results,
        )
