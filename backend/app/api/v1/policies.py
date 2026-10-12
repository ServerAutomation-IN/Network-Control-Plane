"""Policy Management & Governance REST API Router — Network Control Plane"""

import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import UserRole, CurrentUser, require_role
from app.models.policy import NetworkPolicy
from app.schemas.policy import (
    NetworkPolicyCreate,
    NetworkPolicyUpdate,
    NetworkPolicyResponse,
    ComplianceReport,
)
from app.services.policy import PolicyEngine
from app.services.audit import AuditService

router = APIRouter(prefix="/policies", tags=["Policy Governance"])


@router.get("", response_model=List[NetworkPolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all declarative governance policies."""
    stmt = select(NetworkPolicy).order_by(NetworkPolicy.created_at.desc())
    policies = (await db.execute(stmt)).scalars().all()
    return policies


@router.post("", response_model=NetworkPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: NetworkPolicyCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Create a new declarative governance policy specification (Admin only)."""
    now = datetime.now(timezone.utc)
    policy = NetworkPolicy(
        id=f"pol-{uuid.uuid4().hex[:12]}",
        name=payload.name,
        description=payload.description,
        enabled=payload.enabled,
        severity=payload.severity.value,
        rules=payload.rules.model_dump(exclude_none=True),
        created_at=now,
        updated_at=now,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    # Record Audit Event with RBAC actor identity & role
    await AuditService(db).log_event(
        action="CREATE_POLICY",
        resource_type="policy",
        resource_id=policy.id,
        actor=f"{user.user_id} ({user.role.value})",
        risk_level="MEDIUM",
        details={"name": policy.name, "severity": policy.severity, "user_role": user.role.value},
    )

    return policy


@router.get("/compliance", response_model=ComplianceReport)
async def get_compliance_report(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Fetch real-time network policy compliance summary report."""
    engine = PolicyEngine(db)
    report = await engine.get_compliance_report()
    return report


@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def trigger_policy_evaluation(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Trigger immediate manual evaluation of all active policies against inventory networks."""
    engine = PolicyEngine(db)
    results = await engine.evaluate_all()
    return {
        "status": "success",
        "message": f"Evaluated {len(results)} policy-network combinations successfully.",
        "evaluations_count": len(results),
    }


@router.get("/{policy_id}", response_model=NetworkPolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Fetch detailed governance policy specification by ID."""
    stmt = select(NetworkPolicy).where(NetworkPolicy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy '{policy_id}' not found.")
    return policy


@router.put("/{policy_id}", response_model=NetworkPolicyResponse)
async def update_policy(
    policy_id: str,
    payload: NetworkPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Update an existing governance policy specification (Admin only)."""
    stmt = select(NetworkPolicy).where(NetworkPolicy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy '{policy_id}' not found.")

    if payload.name is not None:
        policy.name = payload.name
    if payload.description is not None:
        policy.description = payload.description
    if payload.enabled is not None:
        policy.enabled = payload.enabled
    if payload.severity is not None:
        policy.severity = payload.severity.value
    if payload.rules is not None:
        policy.rules = payload.rules.model_dump(exclude_none=True)

    policy.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(policy)

    await AuditService(db).log_event(
        action="UPDATE_POLICY",
        resource_type="policy",
        resource_id=policy.id,
        actor=f"{user.user_id} ({user.role.value})",
        risk_level="MEDIUM",
        details={"name": policy.name, "user_role": user.role.value},
    )

    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a governance policy specification (Admin only)."""
    stmt = select(NetworkPolicy).where(NetworkPolicy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy '{policy_id}' not found.")

    await db.delete(policy)
    await db.commit()

    await AuditService(db).log_event(
        action="DELETE_POLICY",
        resource_type="policy",
        resource_id=policy_id,
        actor=f"{user.user_id} ({user.role.value})",
        risk_level="HIGH",
        details={"policy_name": policy.name, "user_role": user.role.value},
    )
    return None
