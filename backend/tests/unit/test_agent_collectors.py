"""Unit Tests for Pluggable Runtime Collectors — network-control-plane-agent"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure agent package directory is in sys.path
AGENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "network-control-plane-agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from collectors.base import BaseRuntimeCollector  # noqa: E402
from collectors.docker_collector import DockerCollector  # noqa: E402
from collectors.podman_collector import PodmanCollector  # noqa: E402
from collectors.hyperv_collector import HyperVCollector  # noqa: E402
from collectors.linux_collector import LinuxBridgeCollector  # noqa: E402
from collectors import detect_collector, COLLECTOR_REGISTRY  # noqa: E402


class DummyCollector(BaseRuntimeCollector):
    @property
    def runtime_name(self) -> str:
        return "dummy"

    def is_available(self) -> bool:
        return True

    def get_runtime_info(self):
        return {"provider_type": "dummy", "os": "test-os"}

    def collect_networks(self):
        return [{"name": "dummy-net", "driver": "dummy-driver"}]

    def collect_workloads(self):
        return [{"name": "dummy-box", "status": "running"}]


def test_base_collector_contract():
    """Test BaseRuntimeCollector contract and default ping command handling."""
    collector = DummyCollector()
    assert collector.runtime_name == "dummy"
    assert collector.is_available() is True
    assert collector.get_runtime_info()["provider_type"] == "dummy"
    assert len(collector.collect_networks()) == 1
    assert len(collector.collect_workloads()) == 1

    ping_res = collector.execute_command("PING", {})
    assert ping_res["pong"] is True
    assert ping_res["runtime"] == "dummy"

    with pytest.raises(NotImplementedError):
        collector.execute_command("UNKNOWN_ACTION", {})


def test_docker_collector_metadata_and_fallback():
    """Test DockerCollector returns normalized metadata and gracefully handles offline Docker daemon."""
    collector = DockerCollector()
    assert collector.runtime_name == "docker"

    info = collector.get_runtime_info()
    assert info["provider_type"] == "docker"
    assert "hostname" in info

    # In environments without active Docker socket, collect methods safely return lists without crashing
    nets = collector.collect_networks()
    assert isinstance(nets, list)

    workloads = collector.collect_workloads()
    assert isinstance(workloads, list)

    ping_res = collector.execute_command("PING", {})
    assert ping_res["pong"] is True
    assert ping_res["runtime"] == "docker"


def test_docker_collector_mocked_mutations():
    """Test DockerCollector mutation commands with mocked docker client."""
    collector = DockerCollector()
    mock_client = MagicMock()
    mock_net = MagicMock()
    mock_net.id = "net-doc-123"
    mock_net.name = "prod-isolated-net"
    mock_client.networks.create.return_value = mock_net
    mock_client.networks.get.return_value = mock_net

    with patch.object(collector, "_get_client", return_value=mock_client):
        # CREATE_NETWORK
        res = collector.execute_command(
            "CREATE_NETWORK",
            {
                "name": "prod-isolated-net",
                "driver": "bridge",
                "subnets": [{"subnet": "172.28.0.0/16", "gateway": "172.28.0.1"}],
            },
        )
        assert res["provider_ref_id"] == "net-doc-123"
        assert res["name"] == "prod-isolated-net"
        assert mock_client.networks.create.called

        # DELETE_NETWORK
        del_res = collector.execute_command("DELETE_NETWORK", {"network_ref_id": "net-doc-123"})
        assert del_res["deleted"] is True
        assert mock_net.remove.called

        # ATTACH_ENDPOINT
        att_res = collector.execute_command(
            "ATTACH_ENDPOINT",
            {
                "network_ref_id": "net-doc-123",
                "container_ref_id": "cnt-app-01",
                "ip_address": "172.28.0.5",
            },
        )
        assert att_res["attached"] is True
        assert mock_net.connect.called

        # DETACH_ENDPOINT
        det_res = collector.execute_command(
            "DETACH_ENDPOINT",
            {"network_ref_id": "net-doc-123", "container_ref_id": "cnt-app-01"},
        )
        assert det_res["detached"] is True
        assert mock_net.disconnect.called


def test_podman_collector_discovery_and_commands():
    """Test PodmanCollector discovery and Netavark mutation commands."""
    collector = PodmanCollector()
    assert collector.runtime_name == "podman"

    info = collector.get_runtime_info()
    assert info["provider_type"] == "podman"
    assert info["os"] == "linux"

    nets = collector.collect_networks()
    assert len(nets) >= 1
    assert nets[0]["driver"] == "bridge"
    assert "subnets" in nets[0]

    # Test Podman command mutations
    create_res = collector.execute_command("CREATE_NETWORK", {"name": "podman-isolated-net"})
    assert create_res["name"] == "podman-isolated-net"
    assert "podman-net-" in create_res["provider_ref_id"]

    del_res = collector.execute_command("DELETE_NETWORK", {"network_ref_id": "podman-net-test"})
    assert del_res["deleted"] is True

    att_res = collector.execute_command(
        "ATTACH_ENDPOINT",
        {"network_name": "podman", "container_name": "podman-app-1"},
    )
    assert att_res["attached"] is True

    det_res = collector.execute_command(
        "DETACH_ENDPOINT",
        {"network_name": "podman", "container_name": "podman-app-1"},
    )
    assert det_res["detached"] is True


def test_hyperv_collector_discovery_and_commands():
    """Test HyperVCollector discovery and Virtual Switch mutations."""
    collector = HyperVCollector()
    assert collector.runtime_name == "hyperv"

    info = collector.get_runtime_info()
    assert info["provider_type"] == "hyperv"
    assert info["os"] == "windows"

    nets = collector.collect_networks()
    assert len(nets) >= 2
    switch_names = [n["name"] for n in nets]
    assert "HyperV-External-vSwitch" in switch_names
    assert "HyperV-Internal-vSwitch" in switch_names

    workloads = collector.collect_workloads()
    assert len(workloads) >= 1
    assert workloads[0]["name"] == "hyperv-win-server-2022"
    assert len(workloads[0]["attachments"]) >= 1

    create_res = collector.execute_command("CREATE_NETWORK", {"name": "hv-dmz-vswitch"})
    assert create_res["name"] == "hv-dmz-vswitch"
    assert create_res["driver"] == "hyperv-vswitch"

    del_res = collector.execute_command("DELETE_NETWORK", {"network_ref_id": "hv-vswitch-internal"})
    assert del_res["deleted"] is True


def test_linux_bridge_collector_discovery_and_commands():
    """Test LinuxBridgeCollector discovery and kernel bridge commands."""
    collector = LinuxBridgeCollector()
    assert collector.runtime_name == "linux"

    info = collector.get_runtime_info()
    assert info["provider_type"] == "linux"

    nets = collector.collect_networks()
    assert len(nets) >= 1
    assert nets[0]["driver"] == "linux-bridge"
    assert "subnets" in nets[0]

    workloads = collector.collect_workloads()
    assert len(workloads) >= 1
    assert workloads[0]["image"] == "veth-pair"

    create_res = collector.execute_command("CREATE_NETWORK", {"name": "br-isolated"})
    assert create_res["name"] == "br-isolated"
    assert create_res["driver"] == "linux-bridge"

    del_res = collector.execute_command("DELETE_NETWORK", {"network_ref_id": "linux-br-br0"})
    assert del_res["deleted"] is True


def test_detect_collector_explicit_and_errors():
    """Test detect_collector explicitly instantiating chosen runtime and validating error paths."""
    for runtime_key in COLLECTOR_REGISTRY.keys():
        col = detect_collector(preferred_runtime=runtime_key)
        assert col.runtime_name == runtime_key

    with pytest.raises(ValueError) as exc:
        detect_collector(preferred_runtime="unsupported_cloud_engine")
    assert "Unsupported runtime" in str(exc.value)


def test_detect_collector_auto_detection_priority():
    """Test detect_collector priority fallback ordering."""
    # When Docker is available
    with patch("collectors.docker_collector.DockerCollector.is_available", return_value=True):
        col = detect_collector(preferred_runtime="auto")
        assert col.runtime_name == "docker"

    # When Docker unavailable, Podman available
    with patch("collectors.docker_collector.DockerCollector.is_available", return_value=False), \
         patch("collectors.podman_collector.PodmanCollector.is_available", return_value=True):
        col = detect_collector(preferred_runtime="auto")
        assert col.runtime_name == "podman"

    # When Docker & Podman unavailable, Hyper-V available
    with patch("collectors.docker_collector.DockerCollector.is_available", return_value=False), \
         patch("collectors.podman_collector.PodmanCollector.is_available", return_value=False), \
         patch("collectors.hyperv_collector.HyperVCollector.is_available", return_value=True):
        col = detect_collector(preferred_runtime="auto")
        assert col.runtime_name == "hyperv"

    # When Docker, Podman, Hyper-V unavailable, Linux available
    with patch("collectors.docker_collector.DockerCollector.is_available", return_value=False), \
         patch("collectors.podman_collector.PodmanCollector.is_available", return_value=False), \
         patch("collectors.hyperv_collector.HyperVCollector.is_available", return_value=False), \
         patch("collectors.linux_collector.LinuxBridgeCollector.is_available", return_value=True):
        col = detect_collector(preferred_runtime="auto")
        assert col.runtime_name == "linux"

    # When none are available, fallback returns DockerCollector with offline resilience
    with patch("collectors.docker_collector.DockerCollector.is_available", return_value=False), \
         patch("collectors.podman_collector.PodmanCollector.is_available", return_value=False), \
         patch("collectors.hyperv_collector.HyperVCollector.is_available", return_value=False), \
         patch("collectors.linux_collector.LinuxBridgeCollector.is_available", return_value=False):
        col = detect_collector(preferred_runtime="auto")
        assert col.runtime_name == "docker"
