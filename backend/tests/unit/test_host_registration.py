"""Unit Tests for Host Registration and Fernet TLS Secret Encryption — Network Control Plane"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SecretEncryptor
from app.schemas.host import HostCreate
from app.services.inventory import InventoryService


def test_secret_encryptor_basic():
    """Test SecretEncryptor encrypts and decrypts text accurately."""
    encryptor = SecretEncryptor()
    secret_text = "-----BEGIN CERTIFICATE-----\nMIICXzCCAcgCCQ... \n-----END CERTIFICATE-----"
    
    encrypted_token = encryptor.encrypt(secret_text)
    assert encrypted_token != secret_text
    assert len(encrypted_token) > 0

    decrypted_text = encryptor.decrypt(encrypted_token)
    assert decrypted_text == secret_text


def test_secret_encryptor_empty_input():
    """Test SecretEncryptor handles empty string gracefully."""
    encryptor = SecretEncryptor()
    assert encryptor.encrypt("") == ""
    assert encryptor.decrypt("") == ""


@pytest.mark.asyncio
async def test_register_host_encrypts_tls_cert(db_session: AsyncSession):
    """Test registering host encrypts TLS cert in DB and has_tls_cert property works."""
    service = InventoryService(db_session)
    payload = HostCreate(
        name="Production Worker 1",
        endpoint="tcp://192.168.1.50:2376",
        provider_type="docker",
        environment="production",
        tls_cert="-----BEGIN PRIVATE KEY-----\nSECRET_KEY_DATA\n-----END PRIVATE KEY-----",
    )

    with patch("app.services.inventory.DockerAdapter") as mock_adapter_cls:
        mock_adapter = MagicMock()
        mock_adapter.discover.side_effect = Exception("Host offline in test")
        mock_adapter_cls.return_value = mock_adapter

        host_id = f"host-{payload.name.lower().replace(' ', '-')}"
        encrypted_host = await service.register_host(payload)
        
        assert encrypted_host.id == host_id
        assert encrypted_host.name == "Production Worker 1"
        assert encrypted_host.environment == "production"
        assert encrypted_host.encrypted_tls_cert is not None
        assert encrypted_host.encrypted_tls_cert != payload.tls_cert
        assert encrypted_host.has_tls_cert is True

        decrypted_cert = service.get_decrypted_tls_cert(encrypted_host)
        assert decrypted_cert == payload.tls_cert


@pytest.mark.asyncio
async def test_unregister_host_service(db_session: AsyncSession):
    """Test unregistering a host deletes the entity from DB."""
    service = InventoryService(db_session)
    payload = HostCreate(
        name="Staging Node",
        endpoint="tcp://10.0.0.12:2375",
        environment="staging",
    )

    with patch("app.services.inventory.DockerAdapter") as mock_adapter_cls:
        mock_adapter = MagicMock()
        mock_adapter.discover.side_effect = Exception("Host offline in test")
        mock_adapter_cls.return_value = mock_adapter

        host = await service.register_host(payload)
        host_id = host.id

        result = await service.unregister_host(host_id)
        assert result is True

        # Confirm host is removed
        with pytest.raises(ValueError):
            await service.unregister_host(host_id)
