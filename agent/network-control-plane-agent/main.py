"""CLI Entrypoint for network-control-plane-agent Daemon"""

import argparse
import asyncio
import logging
import sys

from daemon import HostAgentDaemon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("network-control-plane-agent")


def main():
    parser = argparse.ArgumentParser(description="Network Control Plane Remote Host Agent")
    parser.add_argument("--host-id", type=str, help="Unique identifier for this host node")
    parser.add_argument("--control-plane-url", type=str, default="http://localhost:8000", help="Central control plane API URL")
    parser.add_argument("--api-token", type=str, help="Authentication token for agent protocol")
    parser.add_argument("--heartbeat-interval", type=int, default=15, help="Heartbeat interval in seconds")
    parser.add_argument("--snapshot-interval", type=int, default=60, help="Inventory snapshot interval in seconds")
    parser.add_argument(
        "--runtime",
        type=str,
        default="auto",
        choices=["auto", "docker", "podman", "hyperv", "linux"],
        help="Target runtime collector engine (default: auto)",
    )
    parser.add_argument(
        "--socket-path",
        type=str,
        default=None,
        help="Optional custom runtime socket path or endpoint URL",
    )

    args = parser.parse_args()

    daemon = HostAgentDaemon(
        host_id=args.host_id,
        control_plane_url=args.control_plane_url,
        api_token=args.api_token,
        heartbeat_interval=args.heartbeat_interval,
        snapshot_interval=args.snapshot_interval,
        runtime=args.runtime,
        socket_path=args.socket_path,
    )

    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Host agent daemon stopped by user.")
        daemon.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
