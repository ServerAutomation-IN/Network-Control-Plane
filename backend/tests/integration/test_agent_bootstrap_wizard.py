"""Integration Tests for Host Agent Onboarding Wizard & Bootstrap Flow — Network Control Plane"""

import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.bootstrap_token import BootstrapToken
from app.models.host import InfrastructureHost
from app.models.audit import AuditEvent


@pytest.mark.asyncio
async def test_generate_bootstrap_token_and_rbac(db_session):
    """Test generating ephemeral bootstrap token with admin/operator RBAC enforcement."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Non-admin / Viewer role should be blocked with 403
        viewer_resp = await client.post(
            "/api/v1/hosts/bootstrap-token",
            headers={"X-User-Role": "viewer", "X-User-Id": "viewer-user"},
            json={"host_name_hint": "edge-node-01"},
        )
        assert viewer_resp.status_code == 403

        # 2. Admin role should succeed and return ephemeral token
        admin_resp = await client.post(
            "/api/v1/hosts/bootstrap-token",
            headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
            json={"host_name_hint": "edge-node-01"},
        )
        assert admin_resp.status_code == 201
        data = admin_resp.json()
        token = data["token"]
        assert token.startswith("ncp_boot_")
        assert data["expires_in"] == 900
        assert "commands" in data
        assert "linux" in data["commands"]
        assert "windows" in data["commands"]
        assert "docker" in data["commands"]
        assert token in data["commands"]["linux"]

        # Verify Audit Log entry was recorded
        audit_stmt = select(AuditEvent).where(AuditEvent.resource_id == token)
        audit_event = (await db_session.execute(audit_stmt)).scalar_one_or_none()
        assert audit_event is not None
        assert audit_event.action == "HOST_BOOTSTRAP_TOKEN_ISSUED"


@pytest.mark.asyncio
async def test_agent_enrollment_and_bootstrap_lifecycle(db_session):
    """Test full agent enrollment using bootstrap token and lifecycle status progression."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Issue bootstrap token
        token_resp = await client.post(
            "/api/v1/hosts/bootstrap-token",
            headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
            json={"host_name_hint": "prod-edge-gateway-01"},
        )
        token = token_resp.json()["token"]

        # Step 2: Query status while waiting (should be WAITING)
        status_waiting = await client.get(f"/api/v1/hosts/bootstrap-status/{token}")
        assert status_waiting.status_code == 200
        assert status_waiting.json()["status"] == "WAITING"
        assert status_waiting.json()["is_used"] is False

        # Step 3: Agent executes installer script and calls /api/v1/agent/enroll
        enroll_resp = await client.post(
            "/api/v1/agent/enroll",
            json={
                "bootstrap_token": token,
                "hostname": "prod-edge-gateway-01",
                "provider_type": "docker",
                "os": "linux",
                "architecture": "x86_64",
            },
        )
        assert enroll_resp.status_code == 200
        enroll_data = enroll_resp.json()
        host_id = enroll_data["host_id"]
        assert host_id.startswith("host-")
        assert enroll_data["status"] == "ENROLLED"
        assert "api_token" in enroll_data

        # Step 4: Query status after enrollment (should be ONLINE with host object)
        status_online = await client.get(f"/api/v1/hosts/bootstrap-status/{token}")
        assert status_online.status_code == 200
        online_data = status_online.json()
        assert online_data["status"] == "ONLINE"
        assert online_data["is_used"] is True
        assert online_data["host"] is not None
        assert online_data["host"]["id"] == host_id
        assert online_data["host"]["name"] == "prod-edge-gateway-01"

        # Step 5: Verify host was registered in DB
        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
        host = (await db_session.execute(host_stmt)).scalar_one_or_none()
        assert host is not None
        assert host.provider_type == "docker"
        assert host.status == "ONLINE"

        # Step 6: Verify HOST_ENROLLED audit log exists
        audit_stmt = select(AuditEvent).where(
            AuditEvent.action == "HOST_ENROLLED",
            AuditEvent.resource_id == host_id,
        )
        audit_event = (await db_session.execute(audit_stmt)).scalar_one_or_none()
        assert audit_event is not None
        assert audit_event.risk_level == "INFO"


@pytest.mark.asyncio
async def test_agent_enrollment_rejects_reused_and_expired_tokens(db_session):
    """Test security guardrails: tokens cannot be reused or used after expiration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create token
        token_resp = await client.post(
            "/api/v1/hosts/bootstrap-token",
            headers={"X-User-Role": "admin"},
        )
        token = token_resp.json()["token"]

        # First enrollment succeeds
        resp1 = await client.post(
            "/api/v1/agent/enroll",
            json={"bootstrap_token": token, "hostname": "node-01"},
        )
        assert resp1.status_code == 200

        # Second enrollment with same token must fail (single-use constraint)
        resp2 = await client.post(
            "/api/v1/agent/enroll",
            json={"bootstrap_token": token, "hostname": "node-01-reuse-attempt"},
        )
        assert resp2.status_code == 400
        assert "already been consumed" in resp2.json()["detail"]

        # Create expired token directly in DB
        expired_token_id = "ncp_boot_expired_9999"
        expired_record = BootstrapToken(
            id=expired_token_id,
            created_by="admin",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            is_used=False,
        )
        db_session.add(expired_record)
        await db_session.commit()

        # Enrollment with expired token must fail
        exp_resp = await client.post(
            "/api/v1/agent/enroll",
            json={"bootstrap_token": expired_token_id, "hostname": "node-expired"},
        )
        assert exp_resp.status_code == 400
        assert "expired" in exp_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_installer_scripts_endpoint_delivery():
    """Test that install.sh and install.ps1 endpoints serve raw shell scripts over HTTP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Linux shell installer
        sh_resp = await client.get("/install.sh")
        assert sh_resp.status_code == 200
        assert "Network Control Plane" in sh_resp.text
        assert "--control-plane" in sh_resp.text

        # Windows PowerShell installer
        ps_resp = await client.get("/install.ps1")
        assert ps_resp.status_code == 200
        assert "Network Control Plane" in ps_resp.text
        assert "ControlPlane" in ps_resp.text
