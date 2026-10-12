"""GitOps Controller & Auto-Sync Engine — Network Control Plane"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gitops import GitOpsRepository
from app.models.drift import ReconciliationJob
from app.schemas.gitops import (
    GitOpsRepositoryCreate,
    GitSyncResult,
)
from app.schemas.drift import ReconciliationStatus
from app.services.drift import DriftEngine
from app.services.audit import AuditService
from app.services.webhook import WebhookService


class GitOpsSyncService:
    """Controller for Git repository registration, automated manifest pulling, drift evaluation, and auto-reconciliation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_repositories(self) -> List[GitOpsRepository]:
        """List all registered GitOps repositories."""
        stmt = select(GitOpsRepository).order_by(GitOpsRepository.created_at.desc())
        return (await self.db.execute(stmt)).scalars().all()

    async def create_repository(self, payload: GitOpsRepositoryCreate) -> GitOpsRepository:
        """Register a new GitOps manifest repository."""
        repo = GitOpsRepository(
            id=f"repo-{uuid.uuid4().hex[:8]}",
            name=payload.name,
            repo_url=payload.repo_url,
            branch=payload.branch,
            manifest_path=payload.manifest_path,
            auth_token=payload.auth_token,
            sync_interval_seconds=payload.sync_interval_seconds,
            auto_reconcile_low_risk=payload.auto_reconcile_low_risk,
            last_sync_status="SYNCED",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(repo)
        await self.db.commit()
        await self.db.refresh(repo)

        await AuditService(self.db).log_event(
            action="REGISTER_GITOPS_REPO",
            resource_type="gitops_repository",
            resource_id=repo.id,
            actor="admin",
            risk_level="MEDIUM",
            details={"repo_name": repo.name, "url": repo.repo_url, "branch": repo.branch},
        )
        return repo

    async def delete_repository(self, repo_id: str) -> bool:
        """Delete a registered GitOps repository configuration."""
        stmt = select(GitOpsRepository).where(GitOpsRepository.id == repo_id)
        repo = (await self.db.execute(stmt)).scalar_one_or_none()
        if not repo:
            return False
        await self.db.delete(repo)
        await self.db.commit()
        return True

    async def sync_repository(self, repo_id: str, actor: str = "gitops-controller") -> GitSyncResult:
        """Execute pull & drift evaluation for a registered GitOps repository."""
        stmt = select(GitOpsRepository).where(GitOpsRepository.id == repo_id)
        repo = (await self.db.execute(stmt)).scalar_one_or_none()
        if not repo:
            raise ValueError(f"GitOps repository '{repo_id}' not found.")

        repo.last_sync_status = "SYNCING"
        await self.db.commit()

        try:
            # Simulated Git fetch & manifest generation
            commit_hash = hashlib.sha256(f"{repo.repo_url}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:8]
            sample_manifest = f"""apiVersion: network-control-plane/v1
kind: NetworkManifest
metadata:
  name: {repo.name.lower().replace(' ', '-')}-manifest
  source_repo: "{repo.repo_url}"
  commit_hash: "{commit_hash}"
spec:
  networks:
    - name: {repo.name.lower().replace(' ', '_')}_app_net
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      attachable: true
      labels:
        environment: production
        managed-by: gitops-controller
      subnets:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
"""
            drift_engine = DriftEngine(self.db)
            manifest_name, drifts, actions = await drift_engine.compare_manifest_against_runtime(sample_manifest)

            job = ReconciliationJob(
                id=f"rec-{uuid.uuid4().hex[:12]}",
                manifest_name=manifest_name,
                desired_yaml=sample_manifest,
                drifts=[d.model_dump() for d in drifts],
                plan_actions=[a.model_dump() for a in actions],
                status=ReconciliationStatus.PENDING_APPROVAL.value,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(job)

            auto_reconciled = False
            # Check if low-risk auto-reconciliation is enabled
            if repo.auto_reconcile_low_risk and actions and all(a.risk_level == "LOW" for a in actions):
                job.status = ReconciliationStatus.APPROVED.value
                job.approved_by = "gitops-auto-reconciler"
                await drift_engine.execute_reconciliation_plan(job, actor="gitops-auto-reconciler")
                auto_reconciled = True

            repo.last_sync_status = "OUT_OF_SYNC" if (drifts and not auto_reconciled) else "SYNCED"
            repo.last_commit_hash = commit_hash
            repo.last_synced_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Trigger Webhook alerting if drifts detected
            if drifts:
                await WebhookService(self.db).dispatch_event(
                    event_type="DRIFT_DETECTED",
                    details={
                        "repo_id": repo.id,
                        "repo_name": repo.name,
                        "commit_hash": commit_hash,
                        "drifts_count": len(drifts),
                        "auto_reconciled": auto_reconciled,
                    },
                )

            return GitSyncResult(
                repository_id=repo.id,
                status=repo.last_sync_status,
                commit_hash=commit_hash,
                drifts_found=len(drifts),
                actions_generated=len(actions),
                reconciliation_job_id=job.id,
                auto_reconciled=auto_reconciled,
                message=f"GitOps sync completed for '{repo.name}'. Status: {repo.last_sync_status}.",
            )

        except Exception as exc:
            repo.last_sync_status = "FAILED"
            await self.db.commit()
            raise ValueError(f"GitOps Sync Failed for '{repo.name}': {exc}")
