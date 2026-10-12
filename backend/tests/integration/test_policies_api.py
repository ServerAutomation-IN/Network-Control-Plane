"""Integration Tests for Policy Governance REST API & RBAC — Network Control Plane"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_policy_crud_and_rbac_flow():
    """Test full Policy CRUD flow and RBAC role permission enforcement."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Non-admin (viewer) attempting to create policy -> 403 Forbidden
        payload = {
            "name": "Prod Driver Policy",
            "description": "Restrict driver to bridge or overlay",
            "enabled": True,
            "severity": "HIGH",
            "rules": {"allowed_drivers": ["bridge", "overlay"]},
        }
        resp = await client.post("/api/v1/policies", json=payload, headers={"X-User-Role": "viewer"})
        assert resp.status_code == 403

        # 2. Operator attempting to create policy -> 403 Forbidden (Policies creation is Admin only)
        resp = await client.post("/api/v1/policies", json=payload, headers={"X-User-Role": "operator"})
        assert resp.status_code == 403

        # 3. Admin creating policy -> 201 Created
        resp = await client.post("/api/v1/policies", json=payload, headers={"X-User-Role": "admin"})
        assert resp.status_code == 201
        policy_data = resp.json()
        policy_id = policy_data["id"]
        assert policy_data["name"] == "Prod Driver Policy"

        # 4. List policies -> 200 OK for Viewer, Operator, Admin
        resp = await client.get("/api/v1/policies", headers={"X-User-Role": "viewer"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # 5. Trigger policy evaluation -> 200 OK for Operator and Admin
        resp = await client.post("/api/v1/policies/evaluate", headers={"X-User-Role": "operator"})
        assert resp.status_code == 200
        assert "evaluations_count" in resp.json()

        # 6. Fetch compliance report -> 200 OK
        resp = await client.get("/api/v1/policies/compliance", headers={"X-User-Role": "viewer"})
        assert resp.status_code == 200
        report = resp.json()
        assert "compliance_percentage" in report
        assert "total_networks" in report

        # 7. Update policy -> Admin only
        resp = await client.put(
            f"/api/v1/policies/{policy_id}",
            json={"description": "Updated policy description"},
            headers={"X-User-Role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated policy description"

        # 8. Delete policy -> Admin only
        resp = await client.delete(f"/api/v1/policies/{policy_id}", headers={"X-User-Role": "admin"})
        assert resp.status_code == 204


@pytest.mark.asyncio
async def test_pre_execution_policy_blocking():
    """Verify that active governance policies block creation of non-compliant networks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create strict driver policy blocking macvlan
        pol_payload = {
            "name": "Block Macvlan Policy",
            "enabled": True,
            "severity": "CRITICAL",
            "rules": {"blocked_drivers": ["macvlan"]},
        }
        create_pol_resp = await client.post("/api/v1/policies", json=pol_payload, headers={"X-User-Role": "admin"})
        assert create_pol_resp.status_code == 201
        pol_id = create_pol_resp.json()["id"]

        # Attempt to create network with macvlan driver -> expect 400 Bad Request blocked by policy
        net_payload = {
            "host_id": "host-local-docker-host",
            "name": "illegal_macvlan_net",
            "driver": "macvlan",
        }
        net_resp = await client.post("/api/v1/networks", json=net_payload, headers={"X-User-Role": "admin"})
        assert net_resp.status_code == 400
        assert "blocked by governance policies" in net_resp.json()["detail"]

        # Clean up policy
        await client.delete(f"/api/v1/policies/{pol_id}", headers={"X-User-Role": "admin"})
