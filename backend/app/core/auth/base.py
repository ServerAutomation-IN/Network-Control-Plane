"""Base Authentication Provider Contract — Network Control Plane"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAuthProvider(ABC):
    """Abstract interface contract for Enterprise SSO identity providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return friendly title of identity provider."""
        pass

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth2 / OIDC authorization redirect URL."""
        pass

    @abstractmethod
    async def authenticate_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens and map user claims into platform RBAC profile."""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify access token validity against identity provider."""
        pass
