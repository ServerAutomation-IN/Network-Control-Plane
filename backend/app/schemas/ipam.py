"""IPAM Pydantic Schemas — Network Control Plane"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class SubnetDetailSchema(BaseModel):
    network_id: str
    network_name: str
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    driver: str
    subnet: str
    gateway: Optional[str] = None
    total_ips: int
    usable_ips: int
    allocated_ips: int
    utilization_percentage: float

    model_config = ConfigDict(from_attributes=True)


class IPAMConflictSchema(BaseModel):
    conflict_type: str  # OVERLAPPING_SUBNET, GATEWAY_COLLISION, DUPLICATE_STATIC_IP
    severity: str  # WARNING, CRITICAL
    description: str
    affected_network_ids: List[str]
    details: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class IPAMValidationRequest(BaseModel):
    subnet: str = Field(..., description="CIDR subnet representation e.g. 172.25.0.0/16")
    requested_ip: Optional[str] = Field(None, description="Optional IP address to validate within subnet")


class IPAMValidationResponse(BaseModel):
    is_valid: bool
    subnet: str
    requested_ip: Optional[str] = None
    network_address: Optional[str] = None
    broadcast_address: Optional[str] = None
    total_ips: Optional[int] = None
    usable_ips: Optional[int] = None
    is_ip_in_subnet: Optional[bool] = None
    is_ip_reserved: Optional[bool] = None
    errors: List[str] = []
