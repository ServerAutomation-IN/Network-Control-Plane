"""Agent Protocol Definitions for network-control-plane-agent Daemon

Provides protocol data models and API endpoint paths for the remote host agent package.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class AgentHeartbeatRequest(BaseModel):
    host_id: str
    agent_version: str = "1.0.0"
    status: str = "HEALTHY"
    uptime_seconds: float = 0.0
    cpu_utilization_pct: float | None = None
    memory_utilization_pct: float | None = None


class AgentHeartbeatResponse(BaseModel):
    acknowledged: bool = True
    next_heartbeat_interval_seconds: int = 15


class AgentInventorySnapshot(BaseModel):
    host_id: str
    host_info: Dict[str, Any]
    networks: List[Dict[str, Any]] = Field(default_factory=list)
    containers: List[Dict[str, Any]] = Field(default_factory=list)


class AgentEventMessage(BaseModel):
    host_id: str
    event_type: str
    resource_type: str
    resource_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class AgentCommandEnvelope(BaseModel):
    command_id: str
    action: str
    host_id: str | None = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30


class AgentCommandResult(BaseModel):
    command_id: str
    success: bool
    host_id: str | None = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class AgentEnrollRequest(BaseModel):
    bootstrap_token: str
    hostname: str
    provider_type: str = "docker"
    os: str = "linux"
    architecture: str = "x86_64"
    environment: str = "production"


class AgentEnrollResponse(BaseModel):
    host_id: str
    api_token: str
    control_plane_url: str
    status: str = "ENROLLED"
    message: str | None = None


class AgentProtocolEndpoints:
    HEARTBEAT = "/api/v1/agent/heartbeat"
    SNAPSHOT = "/api/v1/agent/snapshot"
    EVENTS = "/api/v1/agent/events"
    COMMANDS = "/api/v1/agent/commands"
    COMMAND_RESULT = "/api/v1/agent/commands/{command_id}/result"
    ENROLL = "/api/v1/agent/enroll"

