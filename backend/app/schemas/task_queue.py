"""Background Execution Queue Schemas — Network Control Plane"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class BackgroundTaskCreate(BaseModel):
    task_type: str = Field(..., description="Task type identifier (e.g. GITOPS_SYNC, UNMANAGED_SWEEP)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task execution parameters")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts on failure")


class BackgroundTaskResponse(BaseModel):
    id: str
    task_type: str
    status: str
    worker_id: str
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error_log: Optional[str]
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class QueueMetricsResponse(BaseModel):
    active_workers: int
    queued_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_latency_ms: float
