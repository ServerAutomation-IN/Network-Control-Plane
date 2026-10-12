"""Desired-State, Drift Detection & GitOps Schemas — Network Control Plane"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class DriftType(str, Enum):
    MISSING_IN_RUNTIME = "MISSING_IN_RUNTIME"
    EXTRA_IN_RUNTIME = "EXTRA_IN_RUNTIME"
    MODIFIED_CONFIG = "MODIFIED_CONFIG"


class ReconciliationStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"


class DesiredSubnetSpec(BaseModel):
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    ip_range: Optional[str] = None


class DesiredNetworkSpec(BaseModel):
    name: str = Field(..., description="Unique name of desired network")
    host_id: str = Field("host-local-docker-host", description="Target infrastructure host ID")
    driver: str = Field("bridge", description="Network driver")
    scope: str = Field("local")
    internal: bool = Field(False)
    attachable: bool = Field(False)
    labels: Dict[str, str] = Field(default_factory=dict)
    subnets: List[DesiredSubnetSpec] = Field(default_factory=list)


class NetworkManifestSpec(BaseModel):
    apiVersion: str = Field("network-control-plane/v1")
    kind: str = Field("NetworkManifest")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    spec: Dict[str, List[DesiredNetworkSpec]] = Field(...)


class DriftDiffItem(BaseModel):
    resource_type: str = "network"
    resource_name: str
    host_id: str
    drift_type: DriftType
    property_name: Optional[str] = None
    desired_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    severity: str = "HIGH"
    details: Optional[str] = None


class ReconciliationAction(BaseModel):
    id: str
    action_type: str  # CREATE_NETWORK, DELETE_NETWORK, UPDATE_NETWORK
    target_resource: str
    host_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"
    reason: str


class ReconciliationCompareRequest(BaseModel):
    desired_yaml: str = Field(..., description="Raw YAML string containing network-control-plane/v1 manifest")
    auto_generate_plan: bool = Field(True)


class ReconciliationJobResponse(BaseModel):
    id: str
    manifest_name: str
    desired_yaml: str
    drifts: List[DriftDiffItem]
    plan_actions: List[ReconciliationAction]
    status: ReconciliationStatus
    approved_by: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
