import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_hosts_api_list_empty(async_client: AsyncClient):
    """Test /api/v1/hosts returns host list when empty."""
    response = await async_client.get("/api/v1/hosts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_networks_api_list_empty(async_client: AsyncClient):
    """Test /api/v1/networks returns network inventory list when empty."""
    response = await async_client.get("/api/v1/networks")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_containers_api_list_empty(async_client: AsyncClient):
    """Test /api/v1/containers returns container inventory list when empty."""
    response = await async_client.get("/api/v1/containers")
    assert response.status_code == 200
    assert response.json() == []
