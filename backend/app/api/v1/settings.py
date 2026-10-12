"""System Settings & Provider Verification REST API Router — Network Control Plane"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import UserRole, CurrentUser, require_role
from app.schemas.settings import (
    ProviderEndpointTestRequest,
    ProviderEndpointTestResponse,
    LLMConnectionTestRequest,
    LLMConnectionTestResponse,
    SystemSettingsResponse,
    SystemSettingsUpdate,
)
from app.services.settings import SettingsService

router = APIRouter(prefix="/settings", tags=["System Settings & Provider Verification"])


@router.get("", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Get current system configuration settings summary."""
    service = SettingsService(db)
    return await service.get_system_settings()


@router.put("", response_model=SystemSettingsResponse)
async def update_system_settings(
    payload: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Update system settings with audit logging."""
    service = SettingsService(db)
    return await service.update_system_settings(payload, actor=f"{user.user_id} ({user.role.value})")


@router.post("/test-provider-endpoint", response_model=ProviderEndpointTestResponse)
async def test_provider_endpoint(
    payload: ProviderEndpointTestRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Test real-time reachability and discovery for cloud or hypervisor provider endpoint."""
    service = SettingsService(db)
    return await service.test_provider_endpoint(payload, actor=f"{user.user_id} ({user.role.value})")


@router.post("/test-llm", response_model=LLMConnectionTestResponse)
async def test_llm_connection(
    payload: LLMConnectionTestRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Test real-time connection and model response for Ollama or Cloud LLMs."""
    service = SettingsService(db)
    return await service.test_llm_connection(payload, actor=f"{user.user_id} ({user.role.value})")
