"""Settings & Provider Verification Service — Network Control Plane

Handles cloud/hypervisor endpoint reachability diagnostics, LLM model connection testing, and system settings persistence.
"""

import time
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from app.core.config import settings
from app.models.settings import SystemSetting
from app.providers.factory import ProviderFactory
from app.ai.providers.factory import get_llm_provider
from app.schemas.settings import (
    ProviderEndpointTestRequest,
    ProviderEndpointTestResponse,
    LLMConnectionTestRequest,
    LLMConnectionTestResponse,
    SystemSettingsResponse,
    SystemSettingsUpdate,
)
from app.services.audit import AuditService


class SettingsService:
    """Service orchestrating provider reachability testing, LLM diagnostic verification, and configuration governance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_settings(self) -> SystemSettingsResponse:
        """Fetch system configuration settings summary from PostgreSQL database."""
        result = await self.db.execute(select(SystemSetting))
        db_rows = result.scalars().all()
        db_map = {row.key: row.value for row in db_rows}

        active_llm = db_map.get("active_llm_provider", "ollama")
        ollama_url = db_map.get("ollama_base_url", settings.OLLAMA_BASE_URL)
        ollama_mod = db_map.get("ollama_model", settings.OLLAMA_MODEL)
        openai_url = db_map.get("openai_base_url", "https://api.openai.com/v1")
        openai_mod = db_map.get("openai_model", "gpt-4o")
        azure_url = db_map.get("azure_base_url", "https://your-resource.openai.azure.com/")
        azure_mod = db_map.get("azure_model", "gpt-4o-deployment")
        anthropic_url = db_map.get("anthropic_base_url", "https://api.anthropic.com/v1")
        anthropic_mod = db_map.get("anthropic_model", "claude-3-5-sonnet-20241022")

        # Keep in-memory settings synchronized
        settings.OLLAMA_BASE_URL = ollama_url
        settings.OLLAMA_MODEL = ollama_mod

        return SystemSettingsResponse(
            project_name=settings.PROJECT_NAME,
            api_v1_str=settings.API_V1_STR,
            active_llm_provider=active_llm,
            ollama_base_url=ollama_url,
            ollama_model=ollama_mod,
            openai_base_url=openai_url,
            openai_model=openai_mod,
            openai_api_key_configured=bool(db_map.get("openai_api_key")),
            azure_base_url=azure_url,
            azure_model=azure_mod,
            azure_api_key_configured=bool(db_map.get("azure_api_key")),
            anthropic_base_url=anthropic_url,
            anthropic_model=anthropic_mod,
            anthropic_api_key_configured=bool(db_map.get("anthropic_api_key")),
            active_providers={
                "aws": True,
                "azure": True,
                "gcp": True,
                "vmware": True,
                "nutanix": True,
                "hyperv": True,
                "docker": True,
                "podman": True,
                "kubernetes": True,
            },
            secret_key_configured=bool(settings.SECRET_KEY),
        )

    async def update_system_settings(self, payload: SystemSettingsUpdate, actor: str = "system") -> SystemSettingsResponse:
        """Update system settings with PostgreSQL persistence and audit logging."""
        updates = payload.model_dump(exclude_unset=True)

        for key, value in updates.items():
            if value is None:
                continue
            setting_item = await self.db.get(SystemSetting, key)
            if setting_item:
                setting_item.value = str(value)
            else:
                setting_item = SystemSetting(key=key, value=str(value))
                self.db.add(setting_item)

        await self.db.commit()

        await AuditService(self.db).log_event(
            action="UPDATE_SYSTEM_SETTINGS",
            resource_type="system_settings",
            resource_id="global",
            actor=actor,
            risk_level="MEDIUM",
            details=updates,
        )

        return await self.get_system_settings()


    async def test_provider_endpoint(self, payload: ProviderEndpointTestRequest, actor: str = "system") -> ProviderEndpointTestResponse:
        """Execute real-time reachability diagnostic verification for cloud/hypervisor provider endpoint."""
        start_time = time.perf_counter()
        ptype = payload.provider_type.lower()
        endpoint = payload.endpoint_url or f"{ptype}.corp.internal"

        try:
            adapter = ProviderFactory.get_adapter(provider_type=ptype, endpoint=endpoint)
            is_pingable = await adapter.ping()
            snapshot = await adapter.discover() if is_pingable else {}
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            status_str = "REACHABLE" if is_pingable else "UNREACHABLE"
            msg = f"Successfully communicated with {ptype.upper()} endpoint '{endpoint}'." if is_pingable else f"Endpoint '{endpoint}' is unreachable."

            details = {
                "endpoint": endpoint,
                "version": snapshot.get("version", "N/A"),
                "os": snapshot.get("os", "N/A"),
                "networks_discovered": len(snapshot.get("networks", [])),
                "workloads_discovered": len(snapshot.get("containers", [])),
            }

            await AuditService(self.db).log_event(
                action="TEST_PROVIDER_ENDPOINT",
                resource_type="provider_endpoint",
                resource_id=f"{ptype}:{endpoint}",
                actor=actor,
                risk_level="LOW",
                details={"provider": ptype, "endpoint": endpoint, "status": status_str, "latency_ms": latency_ms},
            )

            return ProviderEndpointTestResponse(
                status=status_str,
                provider_type=ptype,
                endpoint_url=endpoint,
                latency_ms=latency_ms,
                details=details,
                message=msg,
            )
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ProviderEndpointTestResponse(
                status="UNREACHABLE",
                provider_type=ptype,
                endpoint_url=endpoint,
                latency_ms=latency_ms,
                details={"error": str(exc)},
                message=f"Connection test failed for {ptype.upper()}: {str(exc)}",
            )

    async def test_llm_connection(self, payload: LLMConnectionTestRequest, actor: str = "system") -> LLMConnectionTestResponse:
        """Execute real-time connection diagnostic test for local Ollama or Cloud LLM."""
        start_time = time.perf_counter()
        pname = payload.provider_name.lower()
        base_url = payload.base_url or settings.OLLAMA_BASE_URL
        model_name = payload.model or settings.OLLAMA_MODEL

        try:
            llm = get_llm_provider(
                provider_name=pname,
                api_key=payload.api_key,
                model=model_name,
                base_url=base_url,
            )

            verify_res = await llm.verify_connection()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            is_success = verify_res.get("success", False)
            status_str = "CONNECTED" if is_success else "FAILED"
            resp_text = verify_res.get("message", "")

            await AuditService(self.db).log_event(
                action="TEST_LLM_CONNECTION",
                resource_type="llm_provider",
                resource_id=f"{pname}:{model_name}",
                actor=actor,
                risk_level="LOW",
                details={"provider": pname, "model": model_name, "status": status_str, "latency_ms": latency_ms},
            )

            return LLMConnectionTestResponse(
                status=status_str,
                provider_used=llm.get_provider_name(),
                model=model_name,
                latency_ms=latency_ms,
                sample_response=resp_text,
                error_message=None if is_success else resp_text,
            )
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return LLMConnectionTestResponse(
                status="FAILED",
                provider_used=pname,
                model=model_name,
                latency_ms=latency_ms,
                sample_response="",
                error_message=f"LLM Connection failed: {str(exc)}",
            )
