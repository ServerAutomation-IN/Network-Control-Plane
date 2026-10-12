"""Background Execution Queue REST API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import CurrentUser, UserRole, require_role
from app.schemas.task_queue import (
    BackgroundTaskCreate,
    BackgroundTaskResponse,
    QueueMetricsResponse,
)
from app.services.background_queue import BackgroundQueueService

router = APIRouter(prefix="/tasks", tags=["Background Execution Queue"])


@router.get("/queue", response_model=List[BackgroundTaskResponse])
async def list_background_tasks(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List background task queue items and historical execution logs."""
    service = BackgroundQueueService(db)
    return await service.list_tasks(limit=limit)


@router.get("/metrics", response_model=QueueMetricsResponse)
async def get_queue_metrics(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Retrieve queue health metrics, worker stats, and latency telemetry."""
    service = BackgroundQueueService(db)
    return await service.get_queue_metrics()


@router.post("", response_model=BackgroundTaskResponse, status_code=status.HTTP_201_CREATED)
async def enqueue_background_task(
    payload: BackgroundTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Enqueue a new background task for async execution."""
    service = BackgroundQueueService(db)
    return await service.enqueue_task(payload)


@router.post("/{task_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_background_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Cancel a pending or running background queue task."""
    service = BackgroundQueueService(db)
    cancelled = await service.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task '{task_id}' cannot be cancelled.")
    return {"message": f"Task '{task_id}' successfully cancelled."}


@router.post("/{task_id}/retry", response_model=BackgroundTaskResponse)
async def retry_background_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Force retry execution for a failed background task."""
    service = BackgroundQueueService(db)
    try:
        task = await service.retry_task(task_id)
        # Process retried task
        return await service.process_task(task.id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/{task_id}/process", response_model=BackgroundTaskResponse)
async def process_background_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Execute a queued task immediately."""
    service = BackgroundQueueService(db)
    try:
        return await service.process_task(task_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
