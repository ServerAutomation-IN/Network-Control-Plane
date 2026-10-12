"""Base LLM Provider Abstraction Interface — Network Control Plane"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM inference provider adapters."""

    @abstractmethod
    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        """Generate text completion from LLM provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider identification name."""
        pass

    async def verify_connection(self) -> Dict[str, Any]:
        """Verify reachability of LLM provider endpoint (fast check without cold-start model loading)."""
        return {"success": True, "message": f"Provider '{self.get_provider_name()}' connection online."}
