"""Enterprise Secrets & Key Vault Schemas — Network Control Plane"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class KeyVaultConfig(BaseModel):
    provider_type: str = Field("vault", description="Provider type: vault, aws_secrets, azure_vault, local")
    vault_url: Optional[str] = Field("http://localhost:8200", description="Vault URL or Key Vault endpoint URI")
    token_or_secret: Optional[str] = Field(None, description="AppRole / Access token / secret key")
    mount_point: Optional[str] = Field("secret", description="Vault KV engine mount path")
    region: Optional[str] = Field("us-east-1", description="AWS Region or Datacenter region")


class SecretsTestRequest(BaseModel):
    config: KeyVaultConfig = Field(..., description="Key Vault connection parameters to verify")


class SecretsTestResponse(BaseModel):
    status: str  # HEALTHY, UNHEALTHY
    provider: str
    url: Optional[str] = None
    latency_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)
    message: str


class SecretsProviderInfo(BaseModel):
    id: str
    name: str
    description: str
    hsm_backed: bool
    active: bool
