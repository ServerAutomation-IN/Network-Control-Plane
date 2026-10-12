"""Host Agent Daemon Implementation — network-control-plane-agent

Pluggable agent daemon running on remote provider hosts to monitor container/VM runtimes
(Docker, Podman, Hyper-V, Linux Bridges) and synchronize state bidirectionally with the control plane.
"""

import asyncio
import logging
import socket
import time
from typing import Dict, Any, Optional
import httpx

from protocol import (
    AgentHeartbeatRequest,
    AgentProtocolEndpoints,
)
from collectors import (
    BaseRuntimeCollector,
    detect_collector,
)

logger = logging.getLogger("network-control-plane-agent")


class HostAgentDaemon:
    """Agent daemon running on remote provider hosts to monitor runtimes and sync with control plane."""

    def __init__(
        self,
        host_id: str | None = None,
        control_plane_url: str = "http://localhost:8000",
        api_token: str | None = None,
        heartbeat_interval: int = 15,
        snapshot_interval: int = 60,
        command_poll_interval: int = 5,
        runtime: str = "auto",
        socket_path: Optional[str] = None,
        collector: Optional[BaseRuntimeCollector] = None,
    ):
        self.host_id = host_id or f"host-{socket.gethostname().lower()}"
        self.control_plane_url = control_plane_url.rstrip("/")
        self.api_token = api_token
        self.heartbeat_interval = heartbeat_interval
        self.snapshot_interval = snapshot_interval
        self.command_poll_interval = command_poll_interval
        self.running = False
        self.start_time = time.time()
        self.collector: BaseRuntimeCollector = collector or detect_collector(
            preferred_runtime=runtime,
            socket_path=socket_path,
        )

    def get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    async def send_heartbeat(self, http_client: httpx.AsyncClient) -> bool:
        """Send periodic heartbeat ping to central control plane."""
        uptime = time.time() - self.start_time
        payload = AgentHeartbeatRequest(
            host_id=self.host_id,
            status="HEALTHY",
            uptime_seconds=uptime,
        ).model_dump()

        url = f"{self.control_plane_url}{AgentProtocolEndpoints.HEARTBEAT}"
        try:
            resp = await http_client.post(url, json=payload, headers=self.get_headers(), timeout=5.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.warning(f"Heartbeat ping failed: {exc}")
            return False

    def collect_inventory_snapshot(self) -> Dict[str, Any]:
        """Discover local virtual networks, subnets, and workloads using the active runtime collector."""
        runtime_info = self.collector.get_runtime_info()
        networks = self.collector.collect_networks()
        containers = self.collector.collect_workloads()

        return {
            "host_id": self.host_id,
            "host_info": runtime_info,
            "networks": networks,
            "containers": containers,
        }

    def collect_docker_snapshot(self) -> Dict[str, Any]:
        """Backward-compatible alias for collect_inventory_snapshot."""
        return self.collect_inventory_snapshot()

    async def send_snapshot(self, http_client: httpx.AsyncClient, snapshot_data: Dict[str, Any] | None = None) -> bool:
        """Collect local runtime inventory and push snapshot to central control plane."""
        if snapshot_data is None:
            snapshot_data = self.collect_inventory_snapshot()

        url = f"{self.control_plane_url}{AgentProtocolEndpoints.SNAPSHOT}"
        try:
            resp = await http_client.post(url, json=snapshot_data, headers=self.get_headers(), timeout=10.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.warning(f"Snapshot sync failed: {exc}")
            return False

    async def send_event(
        self,
        http_client: httpx.AsyncClient,
        event_type: str,
        resource_type: str,
        resource_id: str,
        attributes: Dict[str, Any],
    ) -> bool:
        """Stream runtime lifecycle event to central control plane."""
        payload = {
            "host_id": self.host_id,
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "attributes": attributes,
        }

        url = f"{self.control_plane_url}{AgentProtocolEndpoints.EVENTS}"
        try:
            resp = await http_client.post(url, json=payload, headers=self.get_headers(), timeout=5.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.warning(f"Event streaming failed: {exc}")
            return False

    def execute_command(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute imperative mutation command using the active runtime collector."""
        result = self.collector.execute_command(action, payload)
        if action.upper() == "PING" and "host_id" not in result:
            result["host_id"] = self.host_id
        return result

    def execute_docker_command(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Backward-compatible alias for execute_command."""
        return self.execute_command(action, payload)

    async def poll_and_execute_commands(self, http_client: httpx.AsyncClient) -> int:
        """Poll control plane for pending commands, execute locally, and submit results."""
        poll_url = f"{self.control_plane_url}{AgentProtocolEndpoints.COMMANDS}?host_id={self.host_id}"
        try:
            resp = await http_client.get(poll_url, headers=self.get_headers(), timeout=10.0)
            if resp.status_code != 200:
                logger.debug(f"Command poll returned status {resp.status_code}")
                return 0

            data = resp.json().get("data", [])
            if not data:
                return 0

            executed_count = 0
            for cmd in data:
                command_id = cmd["command_id"]
                action = cmd["action"]
                payload = cmd.get("payload", {})

                logger.info(f"Agent received command '{command_id}' (action: {action})")
                try:
                    result_data = self.execute_command(action, payload)
                    success = True
                    error_msg = None
                except Exception as exc:
                    logger.error(f"Failed to execute command '{command_id}': {exc}")
                    result_data = {}
                    success = False
                    error_msg = str(exc)

                # Post execution result back to control plane
                result_url = f"{self.control_plane_url}/api/v1/agent/commands/{command_id}/result"
                result_payload = {
                    "command_id": command_id,
                    "host_id": self.host_id,
                    "success": success,
                    "result_data": result_data,
                    "error_message": error_msg,
                }
                try:
                    res_resp = await http_client.post(
                        result_url,
                        json=result_payload,
                        headers=self.get_headers(),
                        timeout=10.0,
                    )
                    if res_resp.status_code == 200:
                        logger.info(f"Command '{command_id}' result acknowledged by control plane")
                        executed_count += 1
                except Exception as post_exc:
                    logger.warning(f"Failed to post result for command '{command_id}': {post_exc}")

            return executed_count
        except Exception as exc:
            logger.debug(f"Command polling error: {exc}")
            return 0

    async def start(self):
        """Start agent daemon execution loop."""
        self.running = True
        logger.info(
            f"Starting network-control-plane-agent for host '{self.host_id}' "
            f"using runtime collector '{self.collector.runtime_name}' targeting '{self.control_plane_url}'"
        )
        async with httpx.AsyncClient() as client:
            heartbeat_counter = 0
            while self.running:
                await self.send_heartbeat(client)
                await self.poll_and_execute_commands(client)

                if heartbeat_counter % max(1, self.snapshot_interval // self.heartbeat_interval) == 0:
                    await self.send_snapshot(client)

                heartbeat_counter += 1
                await asyncio.sleep(self.heartbeat_interval)

    def stop(self):
        """Stop agent daemon execution."""
        self.running = False
