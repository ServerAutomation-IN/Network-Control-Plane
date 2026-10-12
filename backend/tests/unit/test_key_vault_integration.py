"""Unit Tests for Enterprise Key Vault & Secrets Engine — Network Control Plane"""

import pytest
from app.core.secrets.vault import HashiCorpVaultAdapter
from app.core.secrets.aws_secrets import AWSSecretsManagerAdapter
from app.core.secrets.azure_vault import AzureKeyVaultAdapter
from app.core.secrets.local import LocalEncryptedAdapter
from app.core.secrets.factory import SecretsFactory


@pytest.mark.asyncio
async def test_hashicorp_vault_adapter():
    """Test HashiCorp Vault KV v2 engine and health check."""
    adapter = HashiCorpVaultAdapter(vault_url="http://localhost:8200", token="root-token")
    assert adapter.get_provider_name() == "HashiCorp Vault (KV v2)"

    health = await adapter.health_check()
    assert health["status"] in ["HEALTHY", "UNHEALTHY"]
    assert "provider" in health

    secret = await adapter.get_secret("vault://secret/data/ncp/vcenter")
    assert "username" in secret
    assert "password" in secret

    creds = await adapter.get_ephemeral_credentials(role_name="vmware-admin-role", ttl_seconds=600)
    assert "access_key" in creds or "secret_key" in creds


@pytest.mark.asyncio
async def test_aws_secrets_manager_adapter():
    """Test AWS Secrets Manager adapter and STS temporary credentials."""
    adapter = AWSSecretsManagerAdapter(region_name="us-east-1")
    assert adapter.get_provider_name() == "AWS Secrets Manager"

    health = await adapter.health_check()
    assert health["status"] == "HEALTHY"
    assert health["hsm_backed"] is True

    secret = await adapter.get_secret("aws-secret://prod/ncp/aws-creds")
    assert "username" in secret

    sts_creds = await adapter.get_ephemeral_credentials(role_name="ncp-vpc-role")
    assert "access_key" in sts_creds
    assert "session_token" in sts_creds


@pytest.mark.asyncio
async def test_azure_key_vault_adapter():
    """Test Azure Key Vault HSM-backed adapter and Managed Identity token."""
    adapter = AzureKeyVaultAdapter(vault_url="https://ncp-vault.vault.azure.net/")
    assert "Azure Key Vault" in adapter.get_provider_name()

    health = await adapter.health_check()
    assert health["status"] == "HEALTHY"

    secret = await adapter.get_secret("azure-vault://ncp-sp-key")
    assert "client_secret" in secret

    creds = await adapter.get_ephemeral_credentials(role_name="sp-role")
    assert creds["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_secrets_factory_resolution():
    """Test SecretsFactory dynamic adapter instantiation."""
    hv = SecretsFactory.get_provider("vault")
    assert isinstance(hv, HashiCorpVaultAdapter)

    aws = SecretsFactory.get_provider("aws_secrets")
    assert isinstance(aws, AWSSecretsManagerAdapter)

    azure = SecretsFactory.get_provider("azure_vault")
    assert isinstance(azure, AzureKeyVaultAdapter)

    local = SecretsFactory.get_provider("local")
    assert isinstance(local, LocalEncryptedAdapter)
