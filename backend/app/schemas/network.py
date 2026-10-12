"""Network Pydantic Schemas — Network Control Plane"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SubnetSchema(BaseModel):
    subnet: str | None = None
    gateway: str | None = None
    ip_range: str | None = None

    model_config = ConfigDict(from_attributes=True)


NetworkSubnetCreate = SubnetSchema



class NetworkBase(BaseModel):
    name: str = Field(..., description="Unique name of the network")
    driver: str = Field("bridge", description="Network driver: bridge, overlay, macvlan, etc.")
    scope: str = Field("local", description="Scope: local, swarm, global")
    internal: bool = Field(False, description="Restrict external internet routing")
    attachable: bool = Field(False, description="Allow manual container attachment")
    ingress: bool = Field(False, description="Control ingress routing mesh")
    labels: dict = Field(default_factory=dict)
    options: dict = Field(default_factory=dict)


class NetworkCreateRequest(NetworkBase):
    host_id: str = Field("host-local", description="Target host ID")
    subnets: list[SubnetSchema] = Field(default_factory=list)


class NetworkResponse(NetworkBase):
    id: str
    host_id: str
    host_name: str | None = None
    provider_ref_id: str
    created_at: datetime
    subnets: list[SubnetSchema] = []
    container_count: int = 0

    model_config = ConfigDict(from_attributes=True)



class NetworkDeleteSafetyResponse(BaseModel):
    network_id: str
    network_name: str
    risk_level: str  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    attached_containers_count: int
    impacted_containers: list[dict]
    compose_project: str | None = None
    is_safe_to_delete: bool
    risk_factors: list[str]


class ContainerAttachRequest(BaseModel):
    container_id: str = Field(..., description="Target container ID or provider ref ID")
    ip_address: str | None = Field(None, description="Optional static IP address assignment")
    aliases: list[str] = Field(default_factory=list, description="Optional network DNS aliases")
