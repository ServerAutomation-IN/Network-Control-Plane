"""System Settings & Provider Verification Pydantic Schemas — Network Control Plane"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProviderEndpointTestRequest(BaseModel):
    """Payload to request real-time reachability verification for a cloud/hypervisor provider endpoint."""

    provider_type: str = Field(..., description="Provider descriptor: aws, azure, gcp, vmware, nutanix, hyperv, docker, podman, kubernetes")
    endpoint_url: Optional[str] = Field(None, description="Management API endpoint URL or hostname")
    region_or_zone: Optional[str] = Field(None, description="Cloud region or datacenter zone (e.g. us-east-1, eastus)")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Provider auth credentials or parameters")


class ProviderEndpointTestResponse(BaseModel):
    """Result of provider endpoint reachability verification test."""

    status: str = Field(..., description="Reachability status: REACHABLE or UNREACHABLE")
    provider_type: str
    endpoint_url: str
    latency_ms: float
    details: Dict[str, Any] = Field(default_factory=dict, description="Discovered networks, workloads, version metadata")
    message: str


class LLMConnectionTestRequest(BaseModel):
    """Payload to request real-time LLM connection diagnostic test."""

    provider_name: str = Field(..., description="LLM Provider: ollama, openai, azure, anthropic, mock")
    base_url: Optional[str] = Field(None, description="Ollama or custom LLM endpoint URL")
    model: Optional[str] = Field(None, description="Model identifier: llama3, mistral, gpt-4o, claude-3-5-sonnet")
    api_key: Optional[str] = Field(None, description="API Key or bearer secret (masked in response)")
    temperature: float = Field(0.2, description="Sampling temperature")


class LLMConnectionTestResponse(BaseModel):
    """Result of LLM connection diagnostic verification test."""

    status: str = Field(..., description="Connection status: CONNECTED or FAILED")
    provider_used: str
    model: str
    latency_ms: float
    sample_response: str
    error_message: Optional[str] = None


class SystemSettingsResponse(BaseModel):
    """Aggregated system configuration settings overview."""

    project_name: str
    api_v1_str: str
    active_llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_api_key_configured: bool = False
    azure_base_url: str = "https://your-resource.openai.azure.com/"
    azure_model: str = "gpt-4o-deployment"
    azure_api_key_configured: bool = False
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_api_key_configured: bool = False
    active_providers: Dict[str, bool] = Field(default_factory=dict)
    secret_key_configured: bool = True


class SystemSettingsUpdate(BaseModel):
    """Payload to update system configuration settings."""

    active_llm_provider: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    azure_base_url: Optional[str] = None
    azure_model: Optional[str] = None
    azure_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    anthropic_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None

