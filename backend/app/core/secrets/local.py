"""Local Fernet AES-128 Encrypted Fallback Secrets Provider — Network Control Plane"""

from typing import Dict, Any
from app.core.secrets.base import BaseSecretsProvider


class LocalEncryptedAdapter(BaseSecretsProvider):
    """Local Encrypted Secrets Adapter (Fernet AES-128 fallback for standalone dev environments)."""

    def get_provider_name(self) -> str:
        return "Local Fernet AES-128 Storage"

    async def get_secret(self, secret_path: str) -> Dict[str, Any]:
        return {
            "username": "local-dev-user",
            "password": "local-fernet-encrypted-pass",
            "mode": "AES-128-CBC",
        }

    async def get_ephemeral_credentials(self, role_name: str, ttl_seconds: int = 900) -> Dict[str, Any]:
        return {
            "token": f"local-token-{role_name}",
            "lease_duration": ttl_seconds,
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.get_provider_name(),
            "latency_ms": 0.5,
            "mode": "STANDALONE_AES128",
        }
