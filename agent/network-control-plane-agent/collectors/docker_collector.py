"""Docker Engine Runtime Collector — network-control-plane-agent

Collects networks and container workloads from local Docker Engine daemon via docker-py SDK.
Executes imperative Docker networking lifecycle actions.
"""

import logging
import socket
from typing import Any, Dict, List

from collectors.base import BaseRuntimeCollector

logger = logging.getLogger("network-control-plane-agent.collector.docker")


class DockerCollector(BaseRuntimeCollector):
    """Collector interacting directly with local Docker Engine daemon."""

    @property
    def runtime_name(self) -> str:
        return "docker"

    def _get_client(self):
        """Construct Docker SDK client instance."""
        import docker
        if self.socket_path:
            return docker.DockerClient(base_url=self.socket_path)
        return docker.from_env()

    def is_available(self) -> bool:
        """Check if Docker daemon is installed and responsive."""
        try:
            client = self._get_client()
            return bool(client.ping())
        except Exception as exc:
            logger.debug(f"Docker is not available: {exc}")
            return False

    def get_runtime_info(self) -> Dict[str, Any]:
        """Query Docker daemon version and host architecture."""
        try:
            client = self._get_client()
            version_info = client.version() or {}
            return {
                "hostname": socket.gethostname(),
                "provider_type": "docker",
                "docker_version": version_info.get("Version", "unknown"),
                "os": version_info.get("Os", "linux"),
                "architecture": version_info.get("Arch", "x86_64"),
                "environment": "production",
            }
        except Exception as exc:
            logger.warning(f"Failed to query Docker version info: {exc}")
            return {
                "hostname": socket.gethostname(),
                "provider_type": "docker",
                "docker_version": "24.0.0",
                "os": "linux",
                "architecture": "x86_64",
                "environment": "production",
            }

    def collect_networks(self) -> List[Dict[str, Any]]:
        """Discover virtual networks, subnets, and drivers from Docker Engine."""
        try:
            client = self._get_client()
            raw_nets = client.networks.list()
            networks = []
            for net in raw_nets:
                attrs = net.attrs
                ipam = attrs.get("IPAM") or {}
                ipam_config = ipam.get("Config") or []
                subnets = []
                for cfg in ipam_config:
                    subnets.append({
                        "subnet": cfg.get("Subnet"),
                        "gateway": cfg.get("Gateway"),
                        "ip_range": cfg.get("IPRange"),
                    })
                networks.append({
                    "provider_ref_id": attrs.get("Id"),
                    "name": attrs.get("Name"),
                    "driver": attrs.get("Driver"),
                    "scope": attrs.get("Scope", "local"),
                    "internal": attrs.get("Internal", False),
                    "attachable": attrs.get("Attachable", False),
                    "ingress": attrs.get("Ingress", False),
                    "labels": attrs.get("Labels") or {},
                    "options": attrs.get("Options") or {},
                    "subnets": subnets,
                })
            return networks
        except Exception as exc:
            logger.warning(f"Docker network collection fallback: {exc}")
            return []

    def collect_workloads(self) -> List[Dict[str, Any]]:
        """Discover containers and attached network interfaces from Docker Engine."""
        try:
            client = self._get_client()
            raw_cnts = client.containers.list(all=True)
            containers = []
            for cnt in raw_cnts:
                attrs = cnt.attrs
                net_settings = (attrs.get("NetworkSettings") or {}).get("Networks") or {}
                attachments = []
                for net_name, net_data in net_settings.items():
                    if not net_data:
                        continue
                    attachments.append({
                        "network_name": net_name,
                        "network_ref_id": net_data.get("NetworkID"),
                        "ip_address": net_data.get("IPAddress"),
                        "ipv6_address": net_data.get("GlobalIPv6Address"),
                        "mac_address": net_data.get("MacAddress"),
                        "aliases": net_data.get("Aliases") or [],
                    })

                config_attr = attrs.get("Config") or {}
                state_attr = attrs.get("State") or {}
                containers.append({
                    "provider_ref_id": attrs.get("Id"),
                    "name": attrs.get("Name", "").lstrip("/"),
                    "image": config_attr.get("Image"),
                    "status": state_attr.get("Status", "unknown"),
                    "labels": config_attr.get("Labels") or {},
                    "attachments": attachments,
                })
            return containers
        except Exception as exc:
            logger.warning(f"Docker workload collection fallback: {exc}")
            return []

    def execute_command(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute imperative mutation command locally on Docker Engine."""
        action_upper = action.upper()
        if action_upper == "PING":
            return super().execute_command(action, payload)

        try:
            client = self._get_client()
        except Exception as exc:
            raise RuntimeError(f"Failed to connect to local Docker daemon: {exc}")

        if action_upper == "CREATE_NETWORK":
            name = payload.get("name")
            if not name:
                raise ValueError("Missing 'name' in CREATE_NETWORK payload.")

            driver = payload.get("driver", "bridge")
            internal = payload.get("internal", False)
            attachable = payload.get("attachable", False)
            ingress = payload.get("ingress", False)
            labels = payload.get("labels") or {}
            options = payload.get("options") or {}

            # Construct IPAM configuration if subnets provided
            import docker
            ipam_config = None
            raw_subnets = payload.get("subnets") or []
            if raw_subnets:
                pool_configs = []
                for sub in raw_subnets:
                    subnet_val = sub.get("subnet") if isinstance(sub, dict) else getattr(sub, "subnet", None)
                    gateway_val = sub.get("gateway") if isinstance(sub, dict) else getattr(sub, "gateway", None)
                    ip_range_val = sub.get("ip_range") if isinstance(sub, dict) else getattr(sub, "ip_range", None)
                    pool_configs.append(docker.types.IPAMPool(
                        subnet=subnet_val,
                        gateway=gateway_val,
                        iprange=ip_range_val,
                    ))
                ipam_config = docker.types.IPAMConfig(pool_configs=pool_configs)

            net = client.networks.create(
                name=name,
                driver=driver,
                internal=internal,
                attachable=attachable,
                ingress=ingress,
                labels=labels,
                options=options,
                ipam=ipam_config,
            )
            return {"provider_ref_id": net.id, "name": net.name}

        elif action_upper == "DELETE_NETWORK":
            net_ref = payload.get("network_ref_id") or payload.get("name")
            if not net_ref:
                raise ValueError("Missing 'network_ref_id' or 'name' in DELETE_NETWORK payload.")
            net = client.networks.get(net_ref)
            net.remove()
            return {"deleted": True, "network_ref_id": net_ref}

        elif action_upper == "ATTACH_ENDPOINT":
            net_ref = payload.get("network_ref_id") or payload.get("network_name")
            cnt_ref = payload.get("container_ref_id") or payload.get("container_name")
            if not net_ref or not cnt_ref:
                raise ValueError("Missing 'network_ref_id' or 'container_ref_id' in ATTACH_ENDPOINT payload.")
            net = client.networks.get(net_ref)
            kwargs = {}
            if payload.get("ip_address"):
                kwargs["ipv4_address"] = payload["ip_address"]
            if payload.get("aliases"):
                kwargs["aliases"] = payload["aliases"]
            net.connect(container=cnt_ref, **kwargs)
            return {"attached": True, "network_ref_id": net_ref, "container_ref_id": cnt_ref}

        elif action_upper == "DETACH_ENDPOINT":
            net_ref = payload.get("network_ref_id") or payload.get("network_name")
            cnt_ref = payload.get("container_ref_id") or payload.get("container_name")
            if not net_ref or not cnt_ref:
                raise ValueError("Missing 'network_ref_id' or 'container_ref_id' in DETACH_ENDPOINT payload.")
            net = client.networks.get(net_ref)
            net.disconnect(container=cnt_ref)
            return {"detached": True, "network_ref_id": net_ref, "container_ref_id": cnt_ref}

        else:
            raise ValueError(f"Unsupported Docker agent command action: '{action}'")
