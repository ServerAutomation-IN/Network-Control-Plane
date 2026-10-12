"""Integration Tests for Hosts REST API — Network Control Plane"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_hosts_api_register_and_retrieve(async_client: AsyncClient):
    """Test POST /api/v1/hosts registers host with encrypted TLS cert, GET /api/v1/hosts/{id} retrieves it safely."""
    payload = {
        "name": "Edge Fleet Node 1",
        "endpoint": "tcp://172.18.0.10:2376",
        "provider_type": "docker",
        "environment": "edge",
        "tls_cert": "-----BEGIN CERTIFICATE-----\nSECRET_TLS_CONTENT\n-----END CERTIFICATE-----",
    }

    with patch("app.services.inventory.DockerAdapter") as mock_adapter_cls:
        mock_adapter = MagicMock()
        mock_adapter.discover.side_effect = Exception("Remote host offline during test")
        mock_adapter_cls.return_value = mock_adapter

        # 1. Register host
        response = await async_client.post("/api/v1/hosts", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "host-edge-fleet-node-1"
        assert data["name"] == "Edge Fleet Node 1"
        assert data["environment"] == "edge"
        assert data["has_tls_cert"] is True
        # Verify secret tls_cert or encrypted_tls_cert is NOT exposed in response schema
        assert "tls_cert" not in data
        assert "encrypted_tls_cert" not in data

        # 2. Get host by ID
        get_resp = await async_client.get(f"/api/v1/hosts/{data['id']}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["id"] == data["id"]
        assert get_data["has_tls_cert"] is True
        assert "tls_cert" not in get_data
        assert "encrypted_tls_cert" not in get_data

        # 3. Unregister host
        del_resp = await async_client.delete(f"/api/v1/hosts/{data['id']}")
        assert del_resp.status_code == 204

        # 4. Verify host no longer exists
        get_resp_after = await async_client.get(f"/api/v1/hosts/{data['id']}")
        assert get_resp_after.status_code == 404
