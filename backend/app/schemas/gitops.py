"""GitOps Schemas — Network Control Plane"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class GitOpsRepositoryCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Friendly repository name")
    repo_url: str = Field(..., description="Git HTTPS or SSH repository URL")
    branch: str = Field("main", description="Git branch to sync")
    manifest_path: str = Field("deployment/network-manifest.yaml", description="Relative path to manifest YAML")
    auth_token: Optional[str] = Field(None, description="Optional access token or SSH secret")
    sync_interval_seconds: int = Field(300, ge=30, description="Sync polling interval in seconds")
    auto_reconcile_low_risk: bool = Field(False, description="Automatically apply low-risk reconciliation actions")


class GitOpsRepositoryResponse(BaseModel):
    id: str
    name: str
    repo_url: str
    branch: str
    manifest_path: str
    sync_interval_seconds: int
    auto_reconcile_low_risk: bool
    last_sync_status: str
    last_commit_hash: Optional[str]
    last_synced_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GitWebhookPayload(BaseModel):
    repository: Dict[str, Any] = Field(default_factory=dict)
    ref: str = Field("refs/heads/main")
    after: Optional[str] = Field(None, description="Commit hash after push")
    commits: List[Dict[str, Any]] = Field(default_factory=list)


class GitSyncResult(BaseModel):
    repository_id: str
    status: str
    commit_hash: str
    drifts_found: int
    actions_generated: int
    reconciliation_job_id: Optional[str] = None
    auto_reconciled: bool = False
    message: str
