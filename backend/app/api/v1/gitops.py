"""GitOps Manifest Controller REST API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import CurrentUser, UserRole, require_role
from app.schemas.gitops import (
    GitOpsRepositoryCreate,
    GitOpsRepositoryResponse,
    GitWebhookPayload,
    GitSyncResult,
)
from app.services.gitops import GitOpsSyncService

router = APIRouter(prefix="/gitops", tags=["GitOps Automated Sync"])


@router.get("/repositories", response_model=List[GitOpsRepositoryResponse])
async def list_gitops_repositories(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all registered GitOps desired-state manifest repositories."""
    service = GitOpsSyncService(db)
    return await service.list_repositories()


@router.post("/repositories", response_model=GitOpsRepositoryResponse, status_code=status.HTTP_201_CREATED)
async def register_gitops_repository(
    payload: GitOpsRepositoryCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Register a new GitOps manifest repository for automated polling and drift detection."""
    service = GitOpsSyncService(db)
    return await service.create_repository(payload)


@router.delete("/repositories/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gitops_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Unregister a GitOps repository."""
    service = GitOpsSyncService(db)
    deleted = await service.delete_repository(repo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GitOps repository '{repo_id}' not found.")


@router.post("/repositories/{repo_id}/sync", response_model=GitSyncResult)
async def trigger_gitops_sync(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Trigger manual Git sync pull, compute infrastructure drift, and evaluate auto-reconciliation."""
    service = GitOpsSyncService(db)
    try:
        return await service.sync_repository(repo_id, actor=f"{user.user_id} ({user.role.value})")
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/webhook", response_model=GitSyncResult)
async def process_git_webhook(
    payload: GitWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming GitHub/GitLab push webhook events to trigger instant GitOps sync."""
    service = GitOpsSyncService(db)
    repos = await service.list_repositories()
    if not repos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered GitOps repositories configured.")

    # Trigger sync for the first matching repository
    repo = repos[0]
    return await service.sync_repository(repo.id, actor="git-webhook-trigger")
