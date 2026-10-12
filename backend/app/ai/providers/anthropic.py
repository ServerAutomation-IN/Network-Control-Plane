"""Anthropic Provider Adapter — Network Control Plane"""

from typing import Optional
import httpx
from app.ai.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic Claude API (claude-3-5-sonnet)."""

    def __init__(self, api_key: str = "mock-anthropic-key", model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key
        self.model = model

    def get_provider_name(self) -> str:
        return f"Anthropic ({self.model})"

    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt or "You are an AI pair-programming assistant for Network Control Plane.",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    return resp.json()["content"][0]["text"]
                return f"[Anthropic Error {resp.status_code}] {resp.text}"
        except Exception as exc:
            return f"[Anthropic Connection Error] {exc}"
