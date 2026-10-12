"""Secrets Provider Factory — Network Control Plane"""

from typing import Dict, Any, Optional
from app.core.secrets.base import BaseSecretsProvider
from app.core.secrets.vault import HashiCorpVaultAdapter
from app.core.secrets.aws_secrets import AWSSecretsManagerAdapter
from app.core.secrets.azure_vault import AzureKeyVaultAdapter
from app.core.secrets.local import LocalEncryptedAdapter


class SecretsFactory:
    """Factory creating and resolving enterprise key vault provider adapters."""

    _instances: Dict[str, BaseSecretsProvider] = {}

    @classmethod
    def get_provider(
        cls,
        provider_name: str = "vault",
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseSecretsProvider:
        """Instantiate or retrieve secret provider adapter instance."""
        p_name = (provider_name or "vault").lower()
        cfg = config or {}

        if p_name in ["vault", "hashicorp_vault", "hashicorp"]:
            return HashiCorpVaultAdapter(
                vault_url=cfg.get("vault_url", "http://localhost:8200"),
                token=cfg.get("token", "root-token"),
                mount_point=cfg.get("mount_point", "secret"),
            )
        elif p_name in ["aws", "aws_secrets", "aws_secrets_manager"]:
            return AWSSecretsManagerAdapter(region_name=cfg.get("region_name", "us-east-1"))
        elif p_name in ["azure", "azure_vault", "azure_key_vault"]:
            return AzureKeyVaultAdapter(vault_url=cfg.get("vault_url", "https://ncp-vault.vault.azure.net/"))
        else:
            return LocalEncryptedAdapter()
