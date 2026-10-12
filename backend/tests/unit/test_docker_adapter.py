import pytest
from unittest.mock import MagicMock, patch
from app.docker.adapter import DockerAdapter


@pytest.mark.asyncio
async def test_docker_adapter_discover_networks():
    """Test DockerAdapter discover_networks normalizes raw Docker networks."""
    adapter = DockerAdapter()

    # Mock Docker SDK client
    mock_client = MagicMock()
    mock_network = MagicMock()
    mock_network.attrs = {
        "Id": "net-12345",
        "Name": "bridge",
        "Driver": "bridge",
        "Scope": "local",
        "Internal": False,
        "Attachable": False,
        "Ingress": False,
        "Labels": {"environment": "test"},
        "Options": {},
        "IPAM": {
            "Config": [
                {"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}
            ]
        }
    }
    mock_client.networks.list.return_value = [mock_network]

    with patch.object(adapter, "ping", return_value=True):
        with patch.object(adapter.client_wrapper, "get_client", return_value=mock_client):
            networks = await adapter.discover_networks()
            assert len(networks) == 1
            net = networks[0]
            assert net["provider_ref_id"] == "net-12345"
            assert net["name"] == "bridge"
            assert net["driver"] == "bridge"
            assert len(net["subnets"]) == 1
            assert net["subnets"][0]["subnet"] == "172.17.0.0/16"
            assert net["subnets"][0]["gateway"] == "172.17.0.1"


@pytest.mark.asyncio
async def test_docker_adapter_discover_containers():
    """Test DockerAdapter discover_containers normalizes container workloads."""
    adapter = DockerAdapter()

    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.attrs = {
        "Id": "cnt-67890",
        "Name": "/test-app",
        "Config": {"Image": "nginx:alpine", "Labels": {"app": "web"}},
        "State": {"Status": "running"},
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "NetworkID": "net-12345",
                    "IPAddress": "172.17.0.2",
                    "MacAddress": "02:42:ac:11:00:02",
                    "Aliases": ["web"],
                }
            }
        }
    }
    mock_client.containers.list.return_value = [mock_container]

    with patch.object(adapter, "ping", return_value=True):
        with patch.object(adapter.client_wrapper, "get_client", return_value=mock_client):
            containers = await adapter.discover_containers()
            assert len(containers) == 1
            cnt = containers[0]
            assert cnt["provider_ref_id"] == "cnt-67890"
            assert cnt["name"] == "test-app"
            assert cnt["image"] == "nginx:alpine"
            assert len(cnt["attachments"]) == 1
            assert cnt["attachments"][0]["ip_address"] == "172.17.0.2"
