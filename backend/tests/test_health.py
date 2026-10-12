import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test /health endpoint returns status healthy."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["product"] == "Network Control Plane"


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client: AsyncClient):
    """Test /metrics Prometheus endpoint returns metrics text."""
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "python_info" in response.text
