"""Azure OpenAI Provider Adapter — Network Control Plane"""

from typing import Optional
import httpx
from app.ai.providers.base import BaseLLMProvider


class AzureOpenAIProvider(BaseLLMProvider):
    """Adapter for Azure OpenAI service deployment endpoints."""

    def __init__(
        self,
        endpoint: str = "https://example.openai.azure.com",
        api_key: str = "mock-azure-key",
        deployment_id: str = "gpt-4",
        api_version: str = "2024-02-15-preview",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment_id = deployment_id
        self.api_version = api_version

    def get_provider_name(self) -> str:
        return f"Azure OpenAI ({self.deployment_id})"

    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        url = f"{self.endpoint}/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"messages": messages, "temperature": temperature}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                return f"[Azure OpenAI Error {resp.status_code}] {resp.text}"
        except Exception as exc:
            return f"[Azure Connection Error] {exc}"
