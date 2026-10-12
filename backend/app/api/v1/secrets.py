"""Enterprise Secrets & Key Vault REST API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rbac import CurrentUser, UserRole, require_role
from app.schemas.secrets import (
    KeyVaultConfig,
    SecretsProviderInfo,
    SecretsTestRequest,
    SecretsTestResponse,
)
from app.core.secrets.factory import SecretsFactory
from app.services.audit import AuditService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter(prefix="/secrets", tags=["Enterprise Key Vault & Secrets Engine"])


@router.get("/providers", response_model=List[SecretsProviderInfo])
async def list_secrets_providers(
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List supported Enterprise Key Vault providers and zero-trust hardware features."""
    return [
        SecretsProviderInfo(
            id="vault",
            name="HashiCorp Vault (KV v2)",
            description="Dynamic secrets engine, AppRole auth, and KV v2 secret paths",
            hsm_backed=True,
            active=True,
        ),
        SecretsProviderInfo(
            id="aws_secrets",
            name="AWS Secrets Manager",
            description="AWS KMS decryption and IAM Role / STS temporary credentials",
            hsm_backed=True,
            active=False,
        ),
        SecretsProviderInfo(
            id="azure_vault",
            name="Azure Key Vault",
            description="HSM-backed FIPS 140-2 Level 3 protection and Azure Managed Identity",
            hsm_backed=True,
            active=False,
        ),
        SecretsProviderInfo(
            id="local",
            name="Local Fernet AES-128",
            description="Local encrypted secret storage for standalone development",
            hsm_backed=False,
            active=False,
        ),
    ]


@router.post("/test", response_model=SecretsTestResponse)
async def test_key_vault_connection(
    payload: SecretsTestRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Test real-time connection reachability and authentication health for requested Key Vault configuration."""
    cfg = payload.config
    provider_adapter = SecretsFactory.get_provider(
        provider_name=cfg.provider_type,
        config={
            "vault_url": cfg.vault_url,
            "token": cfg.token_or_secret,
            "mount_point": cfg.mount_point,
            "region_name": cfg.region,
        },
    )

    health_res = await provider_adapter.health_check()
    is_healthy = health_res.get("status") == "HEALTHY"

    await AuditService(db).log_event(
        action="TEST_KEY_VAULT_CONNECTION",
        resource_type="key_vault_provider",
        resource_id=cfg.provider_type,
        actor=f"{user.user_id} ({user.role.value})",
        risk_level="LOW",
        details={"status": health_res.get("status"), "provider": provider_adapter.get_provider_name()},
    )

    return SecretsTestResponse(
        status="HEALTHY" if is_healthy else "UNHEALTHY",
        provider=provider_adapter.get_provider_name(),
        url=cfg.vault_url,
        latency_ms=health_res.get("latency_ms", 0.0),
        details=health_res,
        message=f"Key Vault provider '{provider_adapter.get_provider_name()}' responded successfully.",
    )
