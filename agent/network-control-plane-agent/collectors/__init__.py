"""Pluggable Runtime Collectors Package — network-control-plane-agent

Provides extensible collector implementations and automatic runtime detection
for Docker Engine, Podman (Netavark/CNI), Microsoft Hyper-V, and Linux Bridges.
"""

import logging
from typing import Dict, Optional, Type

from collectors.base import BaseRuntimeCollector
from collectors.docker_collector import DockerCollector
from collectors.podman_collector import PodmanCollector
from collectors.hyperv_collector import HyperVCollector
from collectors.linux_collector import LinuxBridgeCollector

logger = logging.getLogger("network-control-plane-agent.collectors")

COLLECTOR_REGISTRY: Dict[str, Type[BaseRuntimeCollector]] = {
    "docker": DockerCollector,
    "podman": PodmanCollector,
    "hyperv": HyperVCollector,
    "linux": LinuxBridgeCollector,
}


def detect_collector(
    preferred_runtime: str = "auto",
    socket_path: Optional[str] = None,
) -> BaseRuntimeCollector:
    """Detect or initialize the appropriate runtime collector.

    Args:
        preferred_runtime: Desired runtime ('auto', 'docker', 'podman', 'hyperv', 'linux').
        socket_path: Optional explicit custom UNIX socket, named pipe, or endpoint URL.

    Returns:
        An instance of BaseRuntimeCollector.
    """
    normalized_runtime = preferred_runtime.lower().strip()

    if normalized_runtime != "auto":
        collector_cls = COLLECTOR_REGISTRY.get(normalized_runtime)
        if not collector_cls:
            valid_keys = ", ".join(COLLECTOR_REGISTRY.keys())
            raise ValueError(
                f"Unsupported runtime '{preferred_runtime}'. Valid options: auto, {valid_keys}"
            )
        collector = collector_cls(socket_path=socket_path)
        logger.info(f"Initialized explicitly requested collector '{collector.runtime_name}'")
        return collector

    # Auto-detection sequence
    logger.info("Auto-detecting available host runtime collector...")

    # 1. Probe Docker
    docker_collector = DockerCollector(socket_path=socket_path)
    if docker_collector.is_available():
        logger.info("Auto-detection selected: Docker Engine collector")
        return docker_collector

    # 2. Probe Podman
    podman_collector = PodmanCollector(socket_path=socket_path)
    if podman_collector.is_available():
        logger.info("Auto-detection selected: Podman Netavark collector")
        return podman_collector

    # 3. Probe Microsoft Hyper-V
    hyperv_collector = HyperVCollector(socket_path=socket_path)
    if hyperv_collector.is_available():
        logger.info("Auto-detection selected: Microsoft Hyper-V collector")
        return hyperv_collector

    # 4. Probe Linux Bridge
    linux_collector = LinuxBridgeCollector(socket_path=socket_path)
    if linux_collector.is_available():
        logger.info("Auto-detection selected: Linux Native Bridge collector")
        return linux_collector

    # Fallback to DockerCollector with resilient offline defaults
    logger.info("No active container runtime responsive; falling back to Docker collector defaults")
    return docker_collector


__all__ = [
    "BaseRuntimeCollector",
    "DockerCollector",
    "PodmanCollector",
    "HyperVCollector",
    "LinuxBridgeCollector",
    "COLLECTOR_REGISTRY",
    "detect_collector",
]
