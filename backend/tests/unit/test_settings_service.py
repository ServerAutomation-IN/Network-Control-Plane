"""Unit Tests for Settings Service — Network Control Plane"""

import pytest
from app.services.settings import SettingsService
from app.schemas.settings import (
    ProviderEndpointTestRequest,
    LLMConnectionTestRequest,
    SystemSettingsUpdate,
)


@pytest.mark.asyncio
async def test_settings_service_get_and_update(db_session):
    """Test retrieving and updating system settings."""
    service = SettingsService(db_session)
    settings_res = await service.get_system_settings()

    assert settings_res.project_name == "Network Control Plane"
    assert settings_res.ollama_base_url is not None
    assert "hyperv" in settings_res.active_providers

    update_payload = SystemSettingsUpdate(
        ollama_base_url="http://ollama-test-host:11434",
        ollama_model="mistral",
    )
    updated_res = await service.update_system_settings(update_payload, actor="admin-test")
    assert updated_res.ollama_base_url == "http://ollama-test-host:11434"
    assert updated_res.ollama_model == "mistral"

    # Verify persistence by instantiating a fresh SettingsService instance
    fresh_service = SettingsService(db_session)
    reloaded_res = await fresh_service.get_system_settings()
    assert reloaded_res.ollama_base_url == "http://ollama-test-host:11434"
    assert reloaded_res.ollama_model == "mistral"


@pytest.mark.asyncio
async def test_settings_service_provider_endpoint_reachability(db_session):
    """Test testing cloud and hypervisor provider endpoints."""
    service = SettingsService(db_session)

    # Test Hyper-V Provider Endpoint
    hv_req = ProviderEndpointTestRequest(
        provider_type="hyperv",
        endpoint_url="hyperv-host-01.corp.internal",
        credentials={"username": "domain\\admin"},
    )
    hv_res = await service.test_provider_endpoint(hv_req, actor="test-user")
    assert hv_res.status == "REACHABLE"
    assert hv_res.provider_type == "hyperv"
    assert hv_res.latency_ms >= 0

    # Test VMware Provider Endpoint
    vmware_req = ProviderEndpointTestRequest(
        provider_type="vmware",
        endpoint_url="vcenter.corp.internal",
    )
    vmware_res = await service.test_provider_endpoint(vmware_req, actor="test-user")
    assert vmware_res.status == "REACHABLE"
    assert vmware_res.provider_type == "vmware"

    # Test Nutanix Provider Endpoint
    nutanix_req = ProviderEndpointTestRequest(
        provider_type="nutanix",
        endpoint_url="prism.corp.internal",
    )
    nutanix_res = await service.test_provider_endpoint(nutanix_req, actor="test-user")
    assert nutanix_res.status == "REACHABLE"
    assert nutanix_res.provider_type == "nutanix"


@pytest.mark.asyncio
async def test_settings_service_llm_connection(db_session):
    """Test LLM provider connection test tool."""
    service = SettingsService(db_session)

    llm_req = LLMConnectionTestRequest(
        provider_name="mock",
        model="mock-gpt4",
    )
    llm_res = await service.test_llm_connection(llm_req, actor="test-user")
    assert llm_res.status == "CONNECTED"
    assert llm_res.latency_ms >= 0
    assert len(llm_res.sample_response) > 0
