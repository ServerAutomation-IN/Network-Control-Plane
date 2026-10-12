"""Unit Tests for Governed AI Agent & LLM Providers — Network Control Plane"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.providers.factory import get_llm_provider
from app.ai.providers.mock import MockLLMProvider
from app.services.ai_assistant import AIAssistantService
from app.schemas.ai import AIQueryRequest


def test_llm_provider_factory():
    """Verify instantiation of all supported LLM provider adapters."""
    mock_p = get_llm_provider("mock")
    assert isinstance(mock_p, MockLLMProvider)
    assert "Mock" in mock_p.get_provider_name()

    ollama_p = get_llm_provider("ollama", model="llama3")
    assert "Ollama" in ollama_p.get_provider_name()

    openai_p = get_llm_provider("openai", model="gpt-4o")
    assert "OpenAI" in openai_p.get_provider_name()

    azure_p = get_llm_provider("azure", model="gpt-4")
    assert "Azure" in azure_p.get_provider_name()

    anthropic_p = get_llm_provider("anthropic", model="claude-3-5-sonnet")
    assert "Anthropic" in anthropic_p.get_provider_name()


@pytest.mark.asyncio
async def test_ai_assistant_nl_query(db_session: AsyncSession):
    """Test Natural Language Query processing over inventory context."""
    service = AIAssistantService(db_session)
    req = AIQueryRequest(prompt="Show production networks and utilization", provider="mock")
    res = await service.process_query(req)

    assert "Mock" in res.provider_used
    assert res.reasoning is not None
    assert res.query_results is not None
    assert "total_hosts" in res.query_results


@pytest.mark.asyncio
async def test_ai_reachability_diagnostic_and_proposal(db_session: AsyncSession):
    """Test service reachability diagnostic and HITL remediation proposal creation."""
    service = AIAssistantService(db_session)
    req = AIQueryRequest(
        prompt="Diagnose why container A cannot reach container B",
        provider="mock",
    )
    res = await service.process_query(req)

    assert res.reachability_status in ["REACHABLE", "UNREACHABLE"]
    assert res.reasoning is not None
