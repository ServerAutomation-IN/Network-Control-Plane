"""Mock LLM Provider Adapter — Network Control Plane

Deterministic mock LLM provider for fast offline unit testing and fallback reasoning.
"""

from typing import Optional
from app.ai.providers.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock Provider for unit and integration testing without external APIs."""

    def __init__(self, response_text: Optional[str] = None):
        self.response_text = response_text

    def get_provider_name(self) -> str:
        return "Mock LLM Provider (Deterministic)"

    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        if self.response_text:
            return self.response_text

        prompt_lower = prompt.lower()
        if "reachability" in prompt_lower or "reach" in prompt_lower or "cannot connect" in prompt_lower:
            return (
                "Based on network graph analysis, the source container and target container reside on isolated networks "
                "with no shared overlay or gateway bridge attachment. Suggest attaching target container to the shared bridge network."
            )
        elif "utilization" in prompt_lower or "capacity" in prompt_lower:
            return "Analyzed IPAM subnet utilization across all active networks. Found 2 networks operating above 75% capacity limit."

        return f"Network Control Plane AI Assistant processed query: '{prompt}'. Inventory and policy state verified."
