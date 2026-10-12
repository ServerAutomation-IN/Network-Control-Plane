"""Remote Host Agent Protocol Schemas — Network Control Plane

Defines strict Pydantic payload models for network-control-plane-agent communication.
Used by both the central backend control plane and the remote host agent daemon.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class AgentHeartbeatRequest(BaseModel):
    """Heartbeat status payload sent periodically by remote host agents."""

    host_id: str
    agent_version: str = "1.0.0"
    status: str = "HEALTHY"
    uptime_seconds: float = 0.0
    cpu_utilization_pct: float | None = None
    memory_utilization_pct: float | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentHeartbeatResponse(BaseModel):
    """Acknowledgement response sent by control plane to remote host agent."""

    acknowledged: bool = True
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_heartbeat_interval_seconds: int = 15


class AgentHostInfo(BaseModel):
    """Host system & runtime environment details."""

    hostname: str
    provider_type: str = "docker"
    docker_version: str = "unknown"
    os: str = "linux"
    architecture: str = "x86_64"
    environment: str = "production"


class AgentSubnetInfo(BaseModel):
    """Network IPAM subnet configuration."""

    subnet: str
    gateway: str | None = None
    ip_range: str | None = None


class AgentNetworkInfo(BaseModel):
    """Discovered network specification from agent host."""

    provider_ref_id: str
    name: str
    driver: str
    scope: str = "local"
    internal: bool = False
    attachable: bool = False
    ingress: bool = False
    labels: Dict[str, str] = Field(default_factory=dict)
    options: Dict[str, str] = Field(default_factory=dict)
    subnets: List[AgentSubnetInfo] = Field(default_factory=list)


class AgentAttachmentInfo(BaseModel):
    """Container network attachment configuration."""

    network_name: str
    network_ref_id: str | None = None
    ip_address: str | None = None
    ipv6_address: str | None = None
    mac_address: str | None = None
    aliases: List[str] = Field(default_factory=list)


class AgentContainerInfo(BaseModel):
    """Discovered container workload from agent host."""

    provider_ref_id: str
    name: str
    image: str
    status: str
    labels: Dict[str, str] = Field(default_factory=dict)
    attachments: List[AgentAttachmentInfo] = Field(default_factory=list)


class AgentInventorySnapshot(BaseModel):
    """Complete inventory payload reported by agent daemon."""

    host_id: str
    host_info: AgentHostInfo
    networks: List[AgentNetworkInfo] = Field(default_factory=list)
    containers: List[AgentContainerInfo] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentEventMessage(BaseModel):
    """Real-time runtime event streamed by agent daemon to control plane."""

    host_id: str
    event_type: str
    resource_type: str
    resource_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentCommandRequest(BaseModel):
    """Imperative command payload dispatched from control plane to remote host agent."""

    command_id: str
    action: str
    host_id: str | None = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Alias for envelope terminology
AgentCommandEnvelope = AgentCommandRequest


class AgentCommandResult(BaseModel):
    """Execution result returned by remote host agent after executing command."""

    command_id: str
    success: bool
    host_id: str | None = None
    error_message: str | None = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


T = TypeVar("T")


class AgentResponseEnvelope(BaseModel, Generic[T]):
    """Standard response envelope wrapper for Agent Protocol endpoints."""

    status: str = "success"
    message: str | None = None
    data: T | None = None


class AgentEnrollRequest(BaseModel):
    """Enrollment request sent by installer script using an ephemeral bootstrap token."""

    bootstrap_token: str
    hostname: str
    provider_type: str = "docker"
    os: str = "linux"
    architecture: str = "x86_64"
    environment: str = "production"


class AgentEnrollResponse(BaseModel):
    """Enrollment response granting persistent host credentials."""

    host_id: str
    api_token: str
    control_plane_url: str
    status: str = "ENROLLED"
    message: str | None = None

