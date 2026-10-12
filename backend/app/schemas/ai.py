"""AI Assistant & HITL Remediation Schemas — Network Control Plane"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class AIActionProposal(BaseModel):
    id: str
    action_type: str  # ATTACH_CONTAINER, DETACH_CONTAINER, CREATE_NETWORK, PRUNE_NETWORKS
    target_resource: str
    host_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str


class AIQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language prompt query or reachability diagnostic request")
    provider: Optional[str] = Field("mock", description="LLM provider: mock, ollama, openai, azure, anthropic")
    source_container: Optional[str] = Field(None, description="Optional source container ID for reachability diagnostic")
    target_container: Optional[str] = Field(None, description="Optional target container ID for reachability diagnostic")


class AIQueryResponse(BaseModel):
    provider_used: str
    prompt: str
    reasoning: str
    query_results: Optional[Dict[str, Any]] = None
    reachability_status: Optional[str] = None  # REACHABLE, UNREACHABLE, PARTIALLY_REACHABLE
    proposal_id: Optional[str] = None
    proposed_actions: List[AIActionProposal] = Field(default_factory=list)


class AIProposalResponse(BaseModel):
    id: str
    user_prompt: str
    diagnostic_type: str
    reasoning_summary: str
    proposed_actions: List[AIActionProposal]
    status: str
    approved_by: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
