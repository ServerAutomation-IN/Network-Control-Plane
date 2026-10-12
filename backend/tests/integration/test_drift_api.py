"""Integration Tests for Drift Detection REST API & GitOps Reconciliation Workflow — Network Control Plane"""

import pytest
from httpx import AsyncClient

SAMPLE_YAML_SPEC = """apiVersion: network-control-plane/v1
kind: NetworkManifest
metadata:
  name: integration-test-manifest
spec:
  networks:
    - name: gitops_integration_net
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      subnets:
        - subnet: 172.31.0.0/16
          gateway: 172.31.0.1
"""


@pytest.mark.asyncio
async def test_drift_compare_approve_execute_workflow(async_client: AsyncClient):
    """Test end-to-end GitOps drift compare, human-in-the-loop approval, and execution workflow."""
    # 1. Compare desired YAML spec against runtime -> 201 Created
    compare_resp = await async_client.post(
        "/api/v1/drift/compare",
        json={"desired_yaml": SAMPLE_YAML_SPEC},
        headers={"X-User-Role": "admin"},
    )
    assert compare_resp.status_code == 201
    job_data = compare_resp.json()
    plan_id = job_data["id"]
    assert job_data["status"] == "PENDING_APPROVAL"
    assert len(job_data["drifts"]) >= 1
    assert len(job_data["plan_actions"]) >= 1

    # 2. Attempting to execute unapproved plan -> 400 Bad Request
    exec_fail_resp = await async_client.post(
        f"/api/v1/drift/plans/{plan_id}/execute",
        headers={"X-User-Role": "admin"},
    )
    assert exec_fail_resp.status_code == 400

    # 3. Human-in-the-Loop Approval -> 200 OK
    approve_resp = await async_client.post(
        f"/api/v1/drift/plans/{plan_id}/approve",
        headers={"X-User-Role": "admin"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
    assert "admin" in approve_resp.json()["approved_by"]

    # 4. Execute approved plan -> 200 OK
    exec_resp = await async_client.post(
        f"/api/v1/drift/plans/{plan_id}/execute",
        headers={"X-User-Role": "admin"},
    )
    assert exec_resp.status_code == 200
    exec_job = exec_resp.json()
    assert exec_job["status"] == "EXECUTED"
    assert exec_job["execution_result"] is not None


@pytest.mark.asyncio
async def test_git_sync_endpoint(async_client: AsyncClient):
    """Test automated Git repository sync endpoint."""
    resp = await async_client.post(
        "/api/v1/drift/git-sync?repo_url=https://github.com/org/network-control-plane-manifests",
        headers={"X-User-Role": "admin"},
    )
    assert resp.status_code == 200
    git_job = resp.json()
    assert "git-synced" in git_job["manifest_name"]
    assert git_job["status"] == "PENDING_APPROVAL"
