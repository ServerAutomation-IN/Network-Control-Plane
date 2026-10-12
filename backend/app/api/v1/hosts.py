import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.host import InfrastructureHost
from app.models.bootstrap_token import BootstrapToken
from app.schemas.host import (
    HostCreate,
    HostResponse,
    BootstrapTokenCreate,
    BootstrapTokenResponse,
    BootstrapStatusResponse,
)
from app.services.inventory import InventoryService
from app.services.audit import AuditService
from app.core.rbac import CurrentUser, UserRole, require_role

router = APIRouter(prefix="/hosts", tags=["Hosts"])



@router.get("", response_model=List[HostResponse])
async def list_hosts(db: AsyncSession = Depends(get_db)):
    """List all registered provider hosts."""
    stmt = select(InfrastructureHost)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/fleet/summary")
async def get_fleet_summary(db: AsyncSession = Depends(get_db)):
    """Get aggregated fleet-wide inventory metrics and host statistics."""
    from app.services.fleet_aggregator import FleetAggregatorService
    aggregator = FleetAggregatorService(db)
    return await aggregator.get_fleet_summary()


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: str, db: AsyncSession = Depends(get_db)):
    """Get registered provider host by ID."""
    stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
    result = await db.execute(stmt)
    host = result.scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Host '{host_id}' not found.")
    return host


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def register_host(payload: HostCreate, db: AsyncSession = Depends(get_db)):
    """Register a new provider host encrypting TLS certificates at rest."""
    service = InventoryService(db)
    host = await service.register_host(payload)
    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_host(host_id: str, db: AsyncSession = Depends(get_db)):
    """Unregister a provider host and remove associated inventory."""
    service = InventoryService(db)
    try:
        await service.unregister_host(host_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{host_id}/sync", response_model=HostResponse)
async def sync_host(host_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger manual inventory synchronization for a host."""
    stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
    result = await db.execute(stmt)
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Host '{host_id}' not found.")

    service = InventoryService(db)
    synced_host = await service.sync_host(host_id=host.id, endpoint=host.endpoint)
    return synced_host


@router.post("/health-check")
async def evaluate_fleet_health(db: AsyncSession = Depends(get_db)):
    """Trigger fleet-wide host reachability health check."""
    from app.services.fleet_health import FleetHealthWorker
    worker = FleetHealthWorker(db)
    return await worker.evaluate_fleet_health()


@router.post("/bootstrap-token", response_model=BootstrapTokenResponse, status_code=status.HTTP_201_CREATED)
async def generate_bootstrap_token(
    request: Request,
    payload: Optional[BootstrapTokenCreate] = None,
    current_user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db),
):
    """Generate an ephemeral, single-use bootstrap token for remote edge host onboarding."""
    token_str = f"ncp_boot_{uuid.uuid4().hex}"
    expires_in_seconds = 900  # 15 minutes TTL
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in_seconds)

    hint = payload.host_name_hint if payload else None

    token_record = BootstrapToken(
        id=token_str,
        created_by=current_user.user_id,
        host_name_hint=hint,
        expires_at=expires_at,
        is_used=False,
        created_at=now,
    )
    db.add(token_record)

    # Record Audit Event
    audit_service = AuditService(db)
    await audit_service.log_event(
        action="HOST_BOOTSTRAP_TOKEN_ISSUED",
        resource_type="host_bootstrap",
        resource_id=token_str,
        actor=current_user.user_id,
        risk_level="INFO",
        details={"hint": hint, "expires_in": expires_in_seconds},
    )
    await db.commit()


    base_url = str(request.base_url).rstrip("/")

    commands = {
        "linux": f"curl -sSL {base_url}/install.sh | sudo bash -s -- --control-plane {base_url} --token {token_str}",
        "windows": f"irm {base_url}/install.ps1 | iex; Install-NCPAgent -ControlPlane '{base_url}' -Token '{token_str}'",
        "docker": f"docker run -d --name ncp-agent --restart always -v /var/run/docker.sock:/var/run/docker.sock network-control-plane-agent:latest --control-plane-url {base_url} --api-token {token_str}",
    }

    return BootstrapTokenResponse(
        token=token_str,
        expires_in=expires_in_seconds,
        expires_at=expires_at,
        control_plane_url=base_url,
        commands=commands,
    )


@router.get("/bootstrap-status/{token}", response_model=BootstrapStatusResponse)
async def get_bootstrap_status(token: str, db: AsyncSession = Depends(get_db)):
    """Check the real-time onboarding lifecycle status of an issued bootstrap token."""
    stmt = select(BootstrapToken).where(BootstrapToken.id == token)
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bootstrap token '{token}' not found.",
        )

    now = datetime.now(timezone.utc)

    if token_record.is_used and token_record.assigned_host_id:
        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == token_record.assigned_host_id)
        host_result = await db.execute(host_stmt)
        host = host_result.scalar_one_or_none()
        return BootstrapStatusResponse(
            token=token,
            status="ONLINE",
            is_used=True,
            host=host,
        )

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return BootstrapStatusResponse(
            token=token,
            status="EXPIRED",
            is_used=False,
            host=None,
        )


    return BootstrapStatusResponse(
        token=token,
        status="WAITING",
        is_used=False,
        host=None,
    )

