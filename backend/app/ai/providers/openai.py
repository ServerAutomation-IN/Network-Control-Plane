"""OpenAI Provider Adapter — Network Control Plane"""

from typing import Optional
import httpx
from app.ai.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI API (gpt-4o / gpt-4o-mini)."""

    def __init__(self, api_key: str = "mock-key", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def get_provider_name(self) -> str:
        return f"OpenAI ({self.model})"

    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "temperature": temperature}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                return f"[OpenAI Error {resp.status_code}] {resp.text}"
        except Exception as exc:
            return f"[OpenAI Connection Error] {exc}"
