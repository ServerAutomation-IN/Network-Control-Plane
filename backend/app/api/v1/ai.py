"""AI Assistant & HITL Remediation REST API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import UserRole, CurrentUser, require_role
from app.models.ai import AIProposalJob
from app.schemas.ai import (
    AIQueryRequest,
    AIQueryResponse,
    AIProposalResponse,
)
from app.services.ai_assistant import AIAssistantService
from app.services.audit import AuditService

router = APIRouter(prefix="/ai", tags=["AI Assistant & HITL Governance"])


@router.post("/query", response_model=AIQueryResponse)
async def process_ai_query(
    payload: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Process natural language query or reachability diagnostic prompt."""
    service = AIAssistantService(db)
    response = await service.process_query(payload, actor=f"{user.user_id} ({user.role.value})")
    return response


@router.get("/proposals", response_model=List[AIProposalResponse])
async def list_ai_proposals(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all AI-generated remediation proposals."""
    stmt = select(AIProposalJob).order_by(AIProposalJob.created_at.desc())
    jobs = (await db.execute(stmt)).scalars().all()
    return jobs


@router.get("/proposals/{proposal_id}", response_model=AIProposalResponse)
async def get_ai_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Get details for a specific AI remediation proposal."""
    stmt = select(AIProposalJob).where(AIProposalJob.id == proposal_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI Proposal '{proposal_id}' not found.")
    return job


@router.post("/proposals/{proposal_id}/approve", response_model=AIProposalResponse)
async def approve_ai_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Human-in-the-Loop Approval Gate: Explicitly approve an AI remediation proposal."""
    stmt = select(AIProposalJob).where(AIProposalJob.id == proposal_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI Proposal '{proposal_id}' not found.")

    if job.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal '{proposal_id}' cannot be approved. Current status: '{job.status}'",
        )

    job.status = "APPROVED"
    job.approved_by = f"{user.user_id} ({user.role.value})"
    await db.commit()
    await db.refresh(job)

    await AuditService(db).log_event(
        action="APPROVE_AI_REMEDIATION_PROPOSAL",
        resource_type="ai_proposal",
        resource_id=job.id,
        actor=job.approved_by,
        risk_level="HIGH",
        details={"actions_count": len(job.proposed_actions)},
    )

    return job


@router.post("/proposals/{proposal_id}/execute", response_model=AIProposalResponse)
async def execute_ai_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Execute human-approved AI remediation proposal deterministically."""
    stmt = select(AIProposalJob).where(AIProposalJob.id == proposal_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI Proposal '{proposal_id}' not found.")

    service = AIAssistantService(db)
    try:
        await service.execute_approved_proposal(job, actor=f"{user.user_id} ({user.role.value})")
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return job
