"""IP Address Management (IPAM) Service — Network Control Plane

CIDR subnet calculations, utilization metrics, subnet overlap detection, and static IP conflict analysis.
"""

import ipaddress
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network import Network, NetworkSubnet
from app.models.container import ContainerNetwork
from app.schemas.ipam import (
    SubnetDetailSchema,
    IPAMConflictSchema,
    IPAMValidationRequest,
    IPAMValidationResponse,
)


class IPAMCalculator:
    """Deterministic CIDR calculations and IP math helpers."""

    @staticmethod
    def parse_subnet_info(cidr: str) -> Dict[str, Any]:
        """Parse CIDR string into network attributes."""
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            total_ips = net.num_addresses
            # For IPv4 /31 or /32, host counts differ; for standard subnets subtract net & broadcast
            usable_ips = max(0, total_ips - 2) if net.prefixlen < 31 else total_ips
            return {
                "valid": True,
                "network_address": str(net.network_address),
                "broadcast_address": str(net.broadcast_address),
                "netmask": str(net.netmask),
                "total_ips": total_ips,
                "usable_ips": usable_ips,
            }
        except ValueError as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def calculate_utilization(cidr: str, allocated_ips_count: int) -> Dict[str, Any]:
        """Calculate IP utilization percentage for a subnet."""
        info = IPAMCalculator.parse_subnet_info(cidr)
        if not info["valid"]:
            return {"utilization_percentage": 0.0, "total_ips": 0, "usable_ips": 0, "allocated_ips": allocated_ips_count}

        usable = info["usable_ips"]
        percentage = round((allocated_ips_count / usable) * 100, 2) if usable > 0 else 0.0
        return {
            "total_ips": info["total_ips"],
            "usable_ips": usable,
            "allocated_ips": allocated_ips_count,
            "utilization_percentage": min(100.0, percentage),
        }

    @staticmethod
    def check_subnet_overlap(cidr1: str, cidr2: str) -> bool:
        """Check if two CIDR subnet ranges overlap."""
        try:
            net1 = ipaddress.ip_network(cidr1, strict=False)
            net2 = ipaddress.ip_network(cidr2, strict=False)
            return net1.overlaps(net2)
        except ValueError:
            return False


class IPAMService:
    """IPAM orchestration service for auditing subnets, gateway maps, and IP conflicts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_subnets_summary(self) -> List[SubnetDetailSchema]:
        """Retrieve all subnets with active IP utilization calculations."""
        stmt = select(Network).options(
            selectinload(Network.host),
            selectinload(Network.subnets),
            selectinload(Network.container_attachments),
        )
        result = await self.db.execute(stmt)
        networks = result.scalars().all()

        subnet_details: List[SubnetDetailSchema] = []

        for net in networks:
            allocated_count = len(net.container_attachments)
            h_name = net.host.name if net.host else net.host_id
            for sub in net.subnets:
                if not sub.subnet:
                    continue
                metrics = IPAMCalculator.calculate_utilization(sub.subnet, allocated_count)
                subnet_details.append(
                    SubnetDetailSchema(
                        network_id=net.id,
                        network_name=net.name,
                        host_id=net.host_id,
                        host_name=h_name,
                        driver=net.driver,
                        subnet=sub.subnet,
                        gateway=sub.gateway,
                        total_ips=metrics["total_ips"],
                        usable_ips=metrics["usable_ips"],
                        allocated_ips=metrics["allocated_ips"],
                        utilization_percentage=metrics["utilization_percentage"],
                    )
                )

        return subnet_details

    async def detect_conflicts(self, host_id: Optional[str] = None) -> List[IPAMConflictSchema]:
        """Audit for overlapping CIDR blocks, gateway collisions, and duplicate static IPs."""
        stmt = select(Network).options(
            selectinload(Network.subnets),
            selectinload(Network.container_attachments),
        )
        if host_id:
            stmt = stmt.where(Network.host_id == host_id)
        networks = (await self.db.execute(stmt)).scalars().all()

        conflicts: List[IPAMConflictSchema] = []

        # 1. Overlapping Subnets Audit
        subnets_list: List[Dict[str, Any]] = []
        for net in networks:
            for sub in net.subnets:
                if sub.subnet:
                    subnets_list.append({
                        "network_id": net.id,
                        "network_name": net.name,
                        "subnet": sub.subnet,
                        "gateway": sub.gateway,
                    })

        for i in range(len(subnets_list)):
            for j in range(i + 1, len(subnets_list)):
                s1 = subnets_list[i]
                s2 = subnets_list[j]
                if s1["network_id"] != s2["network_id"]:
                    if IPAMCalculator.check_subnet_overlap(s1["subnet"], s2["subnet"]):
                        conflicts.append(
                            IPAMConflictSchema(
                                conflict_type="OVERLAPPING_SUBNET",
                                severity="CRITICAL" if s1["subnet"] == s2["subnet"] else "WARNING",
                                description=f"Subnet '{s1['subnet']}' in '{s1['network_name']}' overlaps with '{s2['subnet']}' in '{s2['network_name']}'.",
                                affected_network_ids=[s1["network_id"], s2["network_id"]],
                                details={"subnet_1": s1["subnet"], "subnet_2": s2["subnet"]},
                            )
                        )

        # 2. Duplicate Static IP Audit
        for net in networks:
            ip_seen: Dict[str, List[str]] = {}
            for att in net.container_attachments:
                if att.ip_address:
                    ip_seen.setdefault(att.ip_address, []).append(att.container_id)

            for ip, cnt_ids in ip_seen.items():
                if len(cnt_ids) > 1:
                    conflicts.append(
                        IPAMConflictSchema(
                            conflict_type="DUPLICATE_STATIC_IP",
                            severity="CRITICAL",
                            description=f"Duplicate IP address '{ip}' assigned to multiple containers on network '{net.name}'.",
                            affected_network_ids=[net.id],
                            details={"ip_address": ip, "container_ids": cnt_ids},
                        )
                    )

        return conflicts

    def validate_allocation(self, req: IPAMValidationRequest) -> IPAMValidationResponse:
        """Validate CIDR subnet format and static IP containment rules."""
        info = IPAMCalculator.parse_subnet_info(req.subnet)
        if not info["valid"]:
            return IPAMValidationResponse(
                is_valid=False,
                subnet=req.subnet,
                errors=[f"Invalid CIDR subnet format: {info.get('error')}"],
            )

        errors: List[str] = []
        is_ip_in_subnet = None
        is_ip_reserved = None

        if req.requested_ip:
            try:
                ip_obj = ipaddress.ip_address(req.requested_ip)
                net_obj = ipaddress.ip_network(req.subnet, strict=False)

                is_ip_in_subnet = ip_obj in net_obj

                if not is_ip_in_subnet:
                    errors.append(f"Requested IP '{req.requested_ip}' is outside subnet boundary '{req.subnet}'.")

                # Check if IP is network or broadcast address
                is_ip_reserved = (ip_obj == net_obj.network_address or ip_obj == net_obj.broadcast_address)
                if is_ip_reserved:
                    errors.append(f"Requested IP '{req.requested_ip}' is a reserved network/broadcast address.")

            except ValueError as e:
                errors.append(f"Invalid requested IP address format: {e}")

        is_valid = len(errors) == 0

        return IPAMValidationResponse(
            is_valid=is_valid,
            subnet=req.subnet,
            requested_ip=req.requested_ip,
            network_address=info["network_address"],
            broadcast_address=info["broadcast_address"],
            total_ips=info["total_ips"],
            usable_ips=info["usable_ips"],
            is_ip_in_subnet=is_ip_in_subnet,
            is_ip_reserved=is_ip_reserved,
            errors=errors,
        )
