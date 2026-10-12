"""Integration Tests for Governed AI Assistant REST API & HITL Approval Workflow — Network Control Plane"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_query_and_proposal_approval_workflow(async_client: AsyncClient):
    """Test AI query processing, reachability diagnostic, and HITL proposal approval gate."""
    # 1. Post AI query -> 200 OK
    query_resp = await async_client.post(
        "/api/v1/ai/query",
        json={"prompt": "Diagnose inter-container reachability failure", "provider": "mock"},
        headers={"X-User-Role": "admin"},
    )
    assert query_resp.status_code == 200
    res_data = query_resp.json()
    assert "provider_used" in res_data
    assert "reasoning" in res_data

    # 2. List proposals -> 200 OK
    list_resp = await async_client.get("/api/v1/ai/proposals", headers={"X-User-Role": "viewer"})
    assert list_resp.status_code == 200
    proposals = list_resp.json()
    assert isinstance(proposals, list)

    if proposals:
        prop_id = proposals[0]["id"]

        # 3. Approve proposal -> 200 OK
        approve_resp = await async_client.post(
            f"/api/v1/ai/proposals/{prop_id}/approve",
            headers={"X-User-Role": "admin"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "APPROVED"

        # 4. Execute approved proposal -> 200 OK
        exec_resp = await async_client.post(
            f"/api/v1/ai/proposals/{prop_id}/execute",
            headers={"X-User-Role": "admin"},
        )
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "EXECUTED"
