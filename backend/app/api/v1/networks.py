"""Networks API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import UserRole, CurrentUser, require_role
from app.models.network import Network
from app.models.policy import NetworkPolicy
from app.schemas.network import (
    NetworkResponse,
    NetworkCreateRequest,
    NetworkDeleteSafetyResponse,
    ContainerAttachRequest,
)
from app.services.inventory import InventoryService
from app.services.safety import PreDeletionSafetyEngine
from app.services.policy import PolicyEngine

router = APIRouter(prefix="/networks", tags=["Networks"])


@router.get("", response_model=List[NetworkResponse])
async def list_networks(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all normalized networks across managed hosts."""
    stmt = select(Network).options(
        selectinload(Network.host),
        selectinload(Network.subnets),
        selectinload(Network.container_attachments),
    )
    result = await db.execute(stmt)
    networks = result.scalars().all()

    response_data = []
    for net in networks:
        item = NetworkResponse.model_validate(net)
        item.host_name = net.host.name if net.host else net.host_id
        item.container_count = len(net.container_attachments)
        response_data.append(item)

    return response_data


@router.post("", response_model=NetworkResponse, status_code=status.HTTP_201_CREATED)
async def create_network(
    payload: NetworkCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Create a new network on host provider and persist entity."""
    # Pre-execution policy check
    policies_stmt = select(NetworkPolicy).where(NetworkPolicy.enabled == True)
    active_policies = (await db.execute(policies_stmt)).scalars().all()

    engine = PolicyEngine(db)
    all_violations = []
    subnets_list = [s.subnet for s in payload.subnets if hasattr(s, "subnet") and s.subnet] if payload.subnets else []
    for pol in active_policies:
        violations = engine.evaluate_rules(
            driver=payload.driver,
            labels=payload.labels or {},
            subnets=subnets_list,
            internal=payload.internal,
            rules_dict=pol.rules,
            severity=pol.severity,
        )
        if violations:
            all_violations.extend([f"[{pol.name}] {v.message}" for v in violations])

    if all_violations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Network creation blocked by governance policies: {'; '.join(all_violations)}",
        )

    service = InventoryService(db)
    try:
        net = await service.create_network(payload)
        item = NetworkResponse.model_validate(net)
        item.host_name = net.host.name if getattr(net, "host", None) else net.host_id
        item.container_count = 0
        return item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{network_id}", response_model=NetworkResponse)
async def get_network(
    network_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Get details for a specific network."""
    stmt = select(Network).where(Network.id == network_id).options(
        selectinload(Network.host),
        selectinload(Network.subnets),
        selectinload(Network.container_attachments),
    )
    result = await db.execute(stmt)
    net = result.scalar_one_or_none()

    if not net:
        raise HTTPException(status_code=404, detail=f"Network '{network_id}' not found.")

    item = NetworkResponse.model_validate(net)
    item.host_name = net.host.name if net.host else net.host_id
    item.container_count = len(net.container_attachments)
    return item


@router.get("/{network_id}/safety-check", response_model=NetworkDeleteSafetyResponse)
async def get_network_safety_assessment(
    network_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Evaluate pre-deletion safety risk factors for a network."""
    safety_engine = PreDeletionSafetyEngine(db)
    return await safety_engine.evaluate_network_deletion(network_id)


@router.delete("/{network_id}", status_code=status.HTTP_200_OK)
async def delete_network(
    network_id: str,
    force: bool = Query(False, description="Force delete network regardless of attached containers"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Delete a network entity with safety validation."""
    service = InventoryService(db)
    try:
        await service.delete_network(network_id=network_id, force=force)
        return {"status": "success", "message": f"Network '{network_id}' successfully deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{network_id}/containers", status_code=status.HTTP_201_CREATED)
async def attach_container_to_network(
    network_id: str,
    payload: ContainerAttachRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Attach a container workload endpoint to a network."""
    service = InventoryService(db)
    try:
        att = await service.attach_container(network_id=network_id, payload=payload)
        return {"status": "success", "attachment_id": att.id, "container_id": att.container_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{network_id}/containers/{container_id}", status_code=status.HTTP_200_OK)
async def detach_container_from_network(
    network_id: str,
    container_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Detach a container workload endpoint from a network."""
    service = InventoryService(db)
    try:
        await service.detach_container(network_id=network_id, container_id=container_id)
        return {"status": "success", "message": f"Container '{container_id}' detached from network '{network_id}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
