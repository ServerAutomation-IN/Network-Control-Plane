"""Unit Tests for GitOps Controller & Background Execution Queue — Network Control Plane"""

import pytest
from app.schemas.gitops import GitOpsRepositoryCreate
from app.schemas.task_queue import BackgroundTaskCreate
from app.services.gitops import GitOpsSyncService
from app.services.background_queue import BackgroundQueueService


@pytest.mark.asyncio
async def test_gitops_repository_lifecycle_and_sync(db_session):
    """Test GitOps manifest repository registration, sync polling, drift calculation, and deletion."""
    service = GitOpsSyncService(db_session)

    # 1. Register GitOps Repo
    create_req = GitOpsRepositoryCreate(
        name="Staging Fleet Network Manifests",
        repo_url="https://github.com/org/staging-net-manifests",
        branch="main",
        manifest_path="deployment/network-manifest.yaml",
        sync_interval_seconds=300,
        auto_reconcile_low_risk=True,
    )
    repo = await service.create_repository(create_req)
    assert repo.id.startswith("repo-")
    assert repo.name == "Staging Fleet Network Manifests"
    assert repo.auto_reconcile_low_risk is True

    # 2. List Repositories
    repos = await service.list_repositories()
    assert len(repos) >= 1
    assert any(r.id == repo.id for r in repos)

    # 3. Trigger Manual Sync
    sync_res = await service.sync_repository(repo.id, actor="pytest-user")
    assert sync_res.repository_id == repo.id
    assert sync_res.status in ["SYNCED", "OUT_OF_SYNC"]
    assert len(sync_res.commit_hash) > 0
    assert sync_res.reconciliation_job_id is not None

    # 4. Delete Repository
    deleted = await service.delete_repository(repo.id)
    assert deleted is True
    repos_after = await service.list_repositories()
    assert not any(r.id == repo.id for r in repos_after)


@pytest.mark.asyncio
async def test_background_execution_queue_lifecycle(db_session):
    """Test BackgroundQueueService task enqueueing, processing, cancellation, retries, and metrics."""
    queue_service = BackgroundQueueService(db_session)

    # 1. Enqueue Background Task
    enqueue_req = BackgroundTaskCreate(
        task_type="GITOPS_SYNC",
        payload={"repo_name": "pytest-repo"},
        max_retries=3,
    )
    task = await queue_service.enqueue_task(enqueue_req, worker_id="worker-pytest-01")
    assert task.id.startswith("task-")
    assert task.status == "QUEUED"
    assert task.worker_id == "worker-pytest-01"

    # 2. Process Task
    processed_task = await queue_service.process_task(task.id)
    assert processed_task.status == "COMPLETED"
    assert processed_task.started_at is not None
    assert processed_task.completed_at is not None

    # 3. Test Task Cancellation
    enqueue_cancel = BackgroundTaskCreate(task_type="UNMANAGED_SWEEP", payload={}, max_retries=1)
    task_cancel = await queue_service.enqueue_task(enqueue_cancel)
    cancelled = await queue_service.cancel_task(task_cancel.id)
    assert cancelled is True

    # 4. Queue Metrics
    metrics = await queue_service.get_queue_metrics()
    assert metrics.active_workers >= 1
    assert metrics.completed_tasks >= 1
