"""Drift Detection, Reconciliation & GitOps REST API Router — Network Control Plane"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import UserRole, CurrentUser, require_role
from app.models.drift import ReconciliationJob
from app.schemas.drift import (
    ReconciliationCompareRequest,
    ReconciliationJobResponse,
    ReconciliationStatus,
)
from app.services.drift import DriftEngine
from app.services.audit import AuditService

router = APIRouter(prefix="/drift", tags=["Drift & GitOps Reconciliation"])


@router.post("/compare", response_model=ReconciliationJobResponse, status_code=status.HTTP_201_CREATED)
async def compare_desired_state(
    payload: ReconciliationCompareRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Parse desired-state YAML manifest, compute infrastructure drift diffs, and generate reconciliation plan."""
    engine = DriftEngine(db)
    try:
        manifest_name, drifts, actions = await engine.compare_manifest_against_runtime(payload.desired_yaml)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    job = ReconciliationJob(
        id=f"rec-{uuid.uuid4().hex[:12]}",
        manifest_name=manifest_name,
        desired_yaml=payload.desired_yaml,
        drifts=[d.model_dump() for d in drifts],
        plan_actions=[a.model_dump() for a in actions],
        status=ReconciliationStatus.PENDING_APPROVAL.value,
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await AuditService(db).log_event(
        action="DRIFT_COMPARE_MANIFEST",
        resource_type="reconciliation_job",
        resource_id=job.id,
        actor=f"{user.user_id} ({user.role.value})",
        risk_level="MEDIUM",
        details={"manifest": manifest_name, "drifts_count": len(drifts), "actions_count": len(actions)},
    )

    return job


@router.get("/plans", response_model=List[ReconciliationJobResponse])
async def list_reconciliation_plans(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all created reconciliation plans and approval workflow jobs."""
    stmt = select(ReconciliationJob).order_by(ReconciliationJob.created_at.desc())
    jobs = (await db.execute(stmt)).scalars().all()
    return jobs


@router.get("/plans/{plan_id}", response_model=ReconciliationJobResponse)
async def get_reconciliation_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Get detailed specification, diffs, and action plan for a reconciliation job."""
    stmt = select(ReconciliationJob).where(ReconciliationJob.id == plan_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation plan '{plan_id}' not found.")
    return job


@router.post("/plans/{plan_id}/approve", response_model=ReconciliationJobResponse)
async def approve_reconciliation_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Human-in-the-Loop Approval Gate: Explicitly approve a pending reconciliation plan."""
    stmt = select(ReconciliationJob).where(ReconciliationJob.id == plan_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation plan '{plan_id}' not found.")

    if job.status != ReconciliationStatus.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{plan_id}' cannot be approved. Current status: '{job.status}'",
        )

    job.status = ReconciliationStatus.APPROVED.value
    job.approved_by = f"{user.user_id} ({user.role.value})"
    await db.commit()
    await db.refresh(job)

    await AuditService(db).log_event(
        action="APPROVE_RECONCILIATION_PLAN",
        resource_type="reconciliation_job",
        resource_id=job.id,
        actor=job.approved_by,
        risk_level="HIGH",
        details={"manifest": job.manifest_name, "actions_count": len(job.plan_actions)},
    )

    return job


@router.post("/plans/{plan_id}/execute", response_model=ReconciliationJobResponse)
async def execute_reconciliation_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Execute human-approved reconciliation plan actions to fix infrastructure drift."""
    stmt = select(ReconciliationJob).where(ReconciliationJob.id == plan_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation plan '{plan_id}' not found.")

    engine = DriftEngine(db)
    try:
        await engine.execute_reconciliation_plan(job, actor=f"{user.user_id} ({user.role.value})")
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return job


@router.post("/git-sync", response_model=ReconciliationJobResponse)
async def sync_from_git_repository(
    repo_url: str = Query(..., description="Git repository URL or manifest path"),
    manifest_path: str = Query("deployment/network-manifest.yaml"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Fetch desired-state network manifest from Git repository and calculate drift."""
    # Simulated Git fetch / template loader for GitOps workflows
    sample_git_manifest = f"""apiVersion: network-control-plane/v1
kind: NetworkManifest
metadata:
  name: git-synced-{manifest_path.replace('/', '-')[:-5]}
  source_repo: "{repo_url}"
spec:
  networks:
    - name: git_app_frontend_net
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      attachable: true
      labels:
        environment: production
        managed-by: gitops
      subnets:
        - subnet: 172.25.0.0/16
          gateway: 172.25.0.1
"""
    return await compare_desired_state(
        payload=ReconciliationCompareRequest(desired_yaml=sample_git_manifest),
        db=db,
        user=user,
    )
