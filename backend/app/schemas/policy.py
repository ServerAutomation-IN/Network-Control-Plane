"""Declarative Policy & Compliance Schemas — Network Control Plane"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class PolicySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"


class PolicyRulesSpec(BaseModel):
    """Specification of declarative rules evaluated against provider networks."""
    allowed_drivers: Optional[List[str]] = Field(
        default=None,
        description="Allowed network drivers (e.g. ['bridge', 'overlay']). Null allows all drivers.",
    )
    blocked_drivers: Optional[List[str]] = Field(
        default=None,
        description="Explicitly forbidden network drivers (e.g. ['host', 'macvlan']).",
    )
    required_labels: Optional[Dict[str, str]] = Field(
        default=None,
        description="Key-value labels that must be present on networks.",
    )
    required_label_keys: Optional[List[str]] = Field(
        default=None,
        description="Label key names that must be present on networks regardless of value.",
    )
    approved_cidr_ranges: Optional[List[str]] = Field(
        default=None,
        description="CIDR blocks within which network subnets must reside (e.g. ['172.16.0.0/12', '10.0.0.0/8']).",
    )
    require_internal: Optional[bool] = Field(
        default=None,
        description="If True, networks must be marked internal=True.",
    )
    max_subnets_per_network: Optional[int] = Field(
        default=None,
        description="Maximum allowed subnets per network.",
    )


class NetworkPolicyCreate(BaseModel):
    """Payload for creating a declarative network policy."""
    name: str = Field(..., min_length=3, max_length=128, description="Policy name")
    description: Optional[str] = Field(default=None, max_length=256)
    enabled: bool = Field(default=True)
    severity: PolicySeverity = Field(default=PolicySeverity.HIGH)
    rules: PolicyRulesSpec = Field(..., description="Rules to evaluate")


class NetworkPolicyUpdate(BaseModel):
    """Payload for updating an existing network policy."""
    name: Optional[str] = Field(default=None, min_length=3, max_length=128)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    severity: Optional[PolicySeverity] = None
    rules: Optional[PolicyRulesSpec] = None


class NetworkPolicyResponse(BaseModel):
    """Network policy entity API response model."""
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool
    severity: PolicySeverity
    rules: PolicyRulesSpec
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ViolationDetail(BaseModel):
    """Individual rule violation detail."""
    rule_type: str  # driver, label, cidr, internal, capacity
    message: str
    severity: PolicySeverity


class PolicyEvaluationResultResponse(BaseModel):
    """Response model for network policy evaluation outcome."""
    id: str
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    network_id: str
    network_name: str
    host_id: str
    status: ComplianceStatus
    violations: List[ViolationDetail]
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceReport(BaseModel):
    """Overall compliance reporting summary model."""
    total_networks: int
    compliant_count: int
    non_compliant_count: int
    compliance_percentage: float
    violations_by_severity: Dict[str, int]
    results: List[PolicyEvaluationResultResponse]
