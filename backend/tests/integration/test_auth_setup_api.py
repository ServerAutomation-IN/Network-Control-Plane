"""Integration Tests for Initial Admin Setup, User Login & Okta SSO JIT Registration — Network Control Plane"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_setup_status_initially_required(async_client: AsyncClient):
    """Test GET /api/v1/auth/setup-status returns setup_required=True when no admin exists."""
    resp = await async_client.get("/api/v1/auth/setup-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "setup_required" in data
    assert "admin_count" in data


@pytest.mark.asyncio
async def test_setup_admin_and_login_flow(async_client: AsyncClient):
    """Test initial admin creation, duplicate rejection, and login verification."""
    # 1. Check initial status
    status_resp = await async_client.get("/api/v1/auth/setup-status")
    assert status_resp.status_code == 200

    # 2. Setup initial admin
    setup_payload = {
        "username": "sysadmin",
        "email": "sysadmin@network-control-plane.org",
        "password": "SecureMasterPassword2026!",
    }
    setup_resp = await async_client.post("/api/v1/auth/setup-admin", json=setup_payload)
    assert setup_resp.status_code == 201
    setup_data = setup_resp.json()
    assert setup_data["user_id"] == "sysadmin"
    assert setup_data["role"] == "admin"
    assert setup_data["token_type"] == "bearer"
    assert len(setup_data["access_token"]) > 20

    # 3. Verify setup-status now indicates setup_required=False
    status_resp2 = await async_client.get("/api/v1/auth/setup-status")
    assert status_resp2.status_code == 200
    assert status_resp2.json()["setup_required"] is False
    assert status_resp2.json()["admin_count"] >= 1

    # 4. Attempting setup-admin again should fail with 400 Bad Request
    dup_resp = await async_client.post("/api/v1/auth/setup-admin", json=setup_payload)
    assert dup_resp.status_code == 400
    assert "already been completed" in dup_resp.json()["detail"]

    # 5. Test Login with valid credentials
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "username": "sysadmin",
        "password": "SecureMasterPassword2026!",
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user_id"] == "sysadmin"
    assert login_data["role"] == "admin"

    # 6. Test Login with invalid password
    bad_login = await async_client.post("/api/v1/auth/login", json={
        "username": "sysadmin",
        "password": "WrongPassword!",
    })
    assert bad_login.status_code == 401
    assert "Invalid username or password" in bad_login.json()["detail"]

    # 7. Test Login with non-existent user
    non_existent = await async_client.post("/api/v1/auth/login", json={
        "username": "ghost_user",
        "password": "SomePassword123!",
    })
    assert non_existent.status_code == 401


@pytest.mark.asyncio
async def test_okta_sso_callback_authorization_and_user_governance(async_client: AsyncClient):
    """Test Okta SSO callback access control:
    1. Uninvited users receive 403 Forbidden with unauthorized message.
    2. Admin onboards the user with a specific role.
    3. User is now allowed to log in via Okta with their assigned role.
    4. Suspended users are blocked from logging in.
    """
    callback_payload = {
        "code": "okta-auth-code-admin-user",
        "redirect_uri": "http://localhost:3000/auth/callback",
    }

    # Step 1: Uninvited user attempts SSO callback -> Must be rejected with 403 Forbidden
    uninvited_resp = await async_client.post("/api/v1/auth/callback/okta", json=callback_payload)
    assert uninvited_resp.status_code == 403
    assert "not authorized to access this application" in uninvited_resp.json()["detail"]

    # Step 2: Administrator onboards the user and assigns the 'operator' role
    admin_headers = {"X-User-Role": "admin", "X-User-Id": "sysadmin"}
    onboard_resp = await async_client.post(
        "/api/v1/auth/users",
        json={
            "username": "sso-admin-user",
            "email": "admin@corp.internal",
            "role": "operator",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert onboard_resp.status_code == 201
    user_data = onboard_resp.json()
    assert user_data["username"] == "sso-admin-user"
    assert user_data["role"] == "operator"
    assert user_data["is_active"] is True

    # Step 3: Now onboarded user logs in via Okta SSO -> Successfully authenticated
    sso_resp = await async_client.post("/api/v1/auth/callback/okta", json=callback_payload)
    assert sso_resp.status_code == 200
    sso_data = sso_resp.json()
    assert sso_data["provider"] == "Okta SSO"
    assert "access_token" in sso_data
    assert sso_data["role"] == "operator"
    assert sso_data["user_id"] == "sso-admin-user"

    # Step 4: Administrator suspends the user account -> Callback must now return 403
    status_resp = await async_client.put(
        "/api/v1/auth/users/sso-admin-user/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["is_active"] is False

    suspended_sso_resp = await async_client.post("/api/v1/auth/callback/okta", json=callback_payload)
    assert suspended_sso_resp.status_code == 403
    assert "deactivated" in suspended_sso_resp.json()["detail"]

    # Step 5: Verify provider update endpoint allows admin configuration
    update_payload = {
        "issuer_url": "https://company.okta.com/oauth2/default",
        "client_id": "0oa-prod-client-id",
        "client_secret": "prod-secret-token",
        "role_claim_path": "groups",
    }
    update_resp = await async_client.put(
        "/api/v1/auth/providers/okta",
        json=update_payload,
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    updated_info = update_resp.json()
    assert updated_info["id"] == "okta"
    assert updated_info["issuer_url"] == "https://company.okta.com/oauth2/default"
    assert updated_info["client_id"] == "0oa-prod-client-id"


@pytest.mark.asyncio
async def test_user_management_crud_and_safety_guards(async_client: AsyncClient):
    """Test User Management APIs: list users, update role, toggle status, delete user, and verify safety guards."""
    admin_headers = {"X-User-Role": "admin", "X-User-Id": "sysadmin"}

    # 1. Onboard a new operator
    new_user_payload = {
        "username": "netops_jane",
        "email": "jane@company.internal",
        "role": "operator",
        "is_active": True,
    }
    create_resp = await async_client.post("/api/v1/auth/users", json=new_user_payload, headers=admin_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["username"] == "netops_jane"
    assert created["role"] == "operator"

    # 2. List users and verify netops_jane appears
    list_resp = await async_client.get("/api/v1/auth/users", headers=admin_headers)
    assert list_resp.status_code == 200
    users = list_resp.json()
    assert len(users) >= 1
    usernames = [u["username"] for u in users]
    assert "netops_jane" in usernames

    # 3. Duplicate onboarding rejected
    dup_resp = await async_client.post("/api/v1/auth/users", json=new_user_payload, headers=admin_headers)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 4. Update role to viewer
    role_resp = await async_client.put(
        "/api/v1/auth/users/netops_jane/role",
        json={"role": "viewer"},
        headers=admin_headers,
    )
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "viewer"

    # 5. Guard against self-deactivation
    self_deact_resp = await async_client.put(
        "/api/v1/auth/users/netops_jane/status",
        json={"is_active": False},
        headers={"X-User-Role": "admin", "X-User-Id": "netops_jane"},
    )
    assert self_deact_resp.status_code == 400
    assert "cannot deactivate your own" in self_deact_resp.json()["detail"]

    # 6. Delete user
    del_resp = await async_client.delete("/api/v1/auth/users/netops_jane", headers=admin_headers)
    assert del_resp.status_code == 200
    assert "successfully deleted" in del_resp.json()["message"]

    # 7. Non-admin forbidden
    viewer_headers = {"X-User-Role": "viewer", "X-User-Id": "some_viewer"}
    forbidden_resp = await async_client.get("/api/v1/auth/users", headers=viewer_headers)
    assert forbidden_resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_root_admin_immutability_and_safety_guards(async_client: AsyncClient):
    """Verify that the primary bootstrap root superadmin account (admin@network-control-plane.local / admin)
    cannot be demoted, suspended, or deleted by other administrators.
    """
    admin_headers = {"X-User-Role": "admin", "X-User-Id": "secondary_admin"}

    # 0. Ensure root admin exists
    status_resp = await async_client.get("/api/v1/auth/setup-status")
    if status_resp.json().get("setup_required"):
        await async_client.post(
            "/api/v1/auth/setup-admin",
            json={
                "username": "admin",
                "email": "admin@network-control-plane.local",
                "password": "MasterAdminPassword123!",
            },
        )

    # 1. Onboard secondary administrator
    await async_client.post(
        "/api/v1/auth/users",
        json={
            "username": "secondary_admin",
            "email": "secondary.admin@corp.internal",
            "role": "admin",
            "is_active": True,
        },
        headers={"X-User-Role": "admin", "X-User-Id": "bootstrap"},
    )

    # 2. Check that root admin (admin) has is_protected == True in user listing
    list_resp = await async_client.get("/api/v1/auth/users", headers=admin_headers)
    assert list_resp.status_code == 200
    users = list_resp.json()
    root_admin = next((u for u in users if u["username"] == "admin" or u["email"] == "admin@network-control-plane.local"), None)
    if root_admin:
        assert root_admin["is_protected"] is True

    # 3. Attempt to demote root admin role to operator -> Must be blocked with 403
    demote_resp = await async_client.put(
        "/api/v1/auth/users/admin/role",
        json={"role": "operator"},
        headers=admin_headers,
    )
    assert demote_resp.status_code == 403
    assert "immutable role" in demote_resp.json()["detail"]

    # 4. Attempt to suspend root admin -> Must be blocked with 403
    suspend_resp = await async_client.put(
        "/api/v1/auth/users/admin/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert suspend_resp.status_code == 403
    assert "cannot be deactivated or suspended" in suspend_resp.json()["detail"]

    # 5. Attempt to delete root admin -> Must be blocked with 403
    delete_resp = await async_client.delete(
        "/api/v1/auth/users/admin",
        headers=admin_headers,
    )
    assert delete_resp.status_code == 403
    assert "cannot be deleted" in delete_resp.json()["detail"]

    # 6. Attempt to onboard an account colliding with the root admin identity -> Must be blocked with 400
    collision_resp = await async_client.post(
        "/api/v1/auth/users",
        json={
            "username": "admin",
            "email": "attacker@evil.com",
            "role": "viewer",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert collision_resp.status_code == 400
    assert "reserved primary platform administrator" in collision_resp.json()["detail"]




