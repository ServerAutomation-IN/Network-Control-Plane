"""LLM Provider Factory — Network Control Plane"""

from typing import Optional
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.azure import AzureOpenAIProvider
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.mock import MockLLMProvider
from app.core.config import settings


def get_llm_provider(
    provider_name: Optional[str] = "mock",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseLLMProvider:
    """Instantiate and return requested LLM provider instance."""
    name = (provider_name or "mock").lower()

    if name == "ollama":
        return OllamaProvider(
            base_url=base_url or settings.OLLAMA_BASE_URL,
            model=model or settings.OLLAMA_MODEL,
        )
    elif name == "openai":
        return OpenAIProvider(api_key=api_key or "mock-key", model=model or "gpt-4o")
    elif name == "azure":
        return AzureOpenAIProvider(api_key=api_key or "mock-key", deployment_id=model or "gpt-4")
    elif name == "anthropic":
        return AnthropicProvider(api_key=api_key or "mock-key", model=model or "claude-3-5-sonnet-20240620")
    else:
        return MockLLMProvider()
