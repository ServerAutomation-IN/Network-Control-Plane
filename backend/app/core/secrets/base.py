"""Base Secrets Provider Interface — Network Control Plane

Adheres strictly to Invariant A1 (Provider Neutrality) and Invariant A2 (Adapter Isolation).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSecretsProvider(ABC):
    """Abstract contract for dynamic enterprise secrets and key vault providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        pass

    @abstractmethod
    async def get_secret(self, secret_path: str) -> Dict[str, Any]:
        """Fetch secret payload key-value mapping from vault."""
        pass

    @abstractmethod
    async def get_ephemeral_credentials(self, role_name: str, ttl_seconds: int = 900) -> Dict[str, Any]:
        """Generate dynamic short-lived credentials for cloud VPC or hypervisors."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check connection reachability and authentication health of Key Vault."""
        pass
