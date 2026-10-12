"""Integration Tests for Settings API Router — Network Control Plane"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_settings_api_get_and_put(async_client: AsyncClient):
    """Test GET /api/v1/settings and PUT /api/v1/settings endpoints."""
    headers = {"X-User-Role": "admin", "X-User-Id": "admin-1"}

    res = await async_client.get("/api/v1/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "ollama_base_url" in data
    assert "active_providers" in data

    update_payload = {"ollama_base_url": "http://ollama-prod:11434", "ollama_model": "llama3.1"}
    put_res = await async_client.put("/api/v1/settings", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    put_data = put_res.json()
    assert put_data["ollama_base_url"] == "http://ollama-prod:11434"
    assert put_data["ollama_model"] == "llama3.1"


@pytest.mark.asyncio
async def test_settings_api_test_provider_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/settings/test-provider-endpoint."""
    headers = {"X-User-Role": "admin", "X-User-Id": "admin-1"}
    payload = {
        "provider_type": "hyperv",
        "endpoint_url": "hyperv-scvmm.corp.internal",
        "credentials": {"username": "admin"},
    }

    res = await async_client.post("/api/v1/settings/test-provider-endpoint", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REACHABLE"
    assert data["provider_type"] == "hyperv"


@pytest.mark.asyncio
async def test_settings_api_test_llm_connection(async_client: AsyncClient):
    """Test POST /api/v1/settings/test-llm."""
    headers = {"X-User-Role": "admin", "X-User-Id": "admin-1"}
    payload = {
        "provider_name": "mock",
        "model": "gpt-4o",
    }

    res = await async_client.post("/api/v1/settings/test-llm", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "CONNECTED"
    assert "sample_response" in data
