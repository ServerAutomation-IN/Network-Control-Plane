"""Docker Engine Client Wrapper — Network Control Plane

Handles low-level Docker API client instantiation, connection ping, and exception wrapping.
"""

from typing import Any, Dict
import docker
from docker.errors import DockerException


class DockerClientWrapper:
    """Wrapper around docker-py SDK client."""

    def __init__(self, base_url: str = "unix:///var/run/docker.sock"):
        self.base_url = base_url
        self._client: docker.DockerClient | None = None

    def get_client(self) -> docker.DockerClient:
        """Get or initialize Docker SDK client."""
        if self._client is None:
            try:
                self._client = docker.DockerClient(base_url=self.base_url)
            except Exception as e:
                raise RuntimeError(f"Failed to connect to Docker Engine at {self.base_url}: {e}")
        return self._client

    def ping(self) -> bool:
        """Check if Docker Engine is responsive."""
        try:
            client = self.get_client()
            return client.ping()
        except Exception:
            return False

    def get_version(self) -> Dict[str, Any]:
        """Retrieve Docker Engine version details."""
        try:
            client = self.get_client()
            return client.version()
        except Exception as e:
            raise RuntimeError(f"Error fetching Docker version: {e}")
