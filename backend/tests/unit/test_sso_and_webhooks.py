"""Unit Tests for Enterprise SSO & Webhook Integrations — Network Control Plane"""

import pytest
from app.core.auth.jwt import create_access_token, decode_access_token
from app.core.auth.oidc import OIDCAuthProvider
from app.core.rbac import get_current_user, UserRole
from app.schemas.webhook import WebhookSubscriptionCreate
from app.services.webhook import WebhookService


def test_jwt_create_and_decode():
    """Test JWT token signing and decoding payload integrity."""
    data = {"user_id": "test-sso-admin", "role": "admin", "provider": "Keycloak OIDC"}
    token = create_access_token(data)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["user_id"] == "test-sso-admin"
    assert payload["role"] == "admin"
    assert payload["provider"] == "Keycloak OIDC"


def test_rbac_user_extraction():
    """Test get_current_user dependency with Bearer JWT and header fallbacks."""
    # 1. Test JWT authentication
    token = create_access_token({"user_id": "jwt-operator", "role": "operator"})
    user_jwt = get_current_user(authorization=f"Bearer {token}")
    assert user_jwt.user_id == "jwt-operator"
    assert user_jwt.role == UserRole.OPERATOR

    # 2. Test Header fallback authentication
    user_hdr = get_current_user(authorization=None, x_user_id="hdr-admin", x_user_role="admin")
    assert user_hdr.user_id == "hdr-admin"
    assert user_hdr.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_oidc_auth_provider_mock_claims():
    """Test OIDC provider adapter fallback claim generation."""
    provider = OIDCAuthProvider(name="Test Keycloak", issuer_url="http://localhost:8080/realms/master")
    auth_url = provider.get_authorization_url("http://localhost:3000/auth/callback", "state123")
    assert "response_type=code" in auth_url
    assert "redirect_uri=http://localhost:3000/auth/callback" in auth_url

    claims = await provider.authenticate_callback("admin-code-xyz", "http://localhost:3000/auth/callback")
    assert claims["role"] == "admin"
    assert "user_id" in claims
    assert claims["provider"] == "Test Keycloak"


def test_okta_oidc_authorization_url():
    """Test Okta-specific /v1/authorize endpoint generation."""
    provider = OIDCAuthProvider(
        name="Okta SSO",
        issuer_url="https://integrator-5964187.okta.com/oauth2/default",
        client_id="0oa18llzujr8xxpfk698",
    )
    auth_url = provider.get_authorization_url("http://localhost:3001/auth/callback", "xyz123")
    assert "https://integrator-5964187.okta.com/oauth2/default/v1/authorize" in auth_url
    assert "client_id=0oa18llzujr8xxpfk698" in auth_url
    assert "redirect_uri=http://localhost:3001/auth/callback" in auth_url


@pytest.mark.asyncio
async def test_webhook_service_lifecycle(db_session):
    """Test webhook subscription CRUD operations, HMAC signature computation, and test delivery ping."""
    service = WebhookService(db_session)

    # 1. Create Webhook Subscription
    create_req = WebhookSubscriptionCreate(
        name="Slack Production Alerts",
        channel_type="slack",
        target_url="https://hooks.slack.com/services/test/mock/webhook",
        secret_token="secret-token-12345",
        subscribed_events=["AUDIT_EVENT", "DRIFT_DETECTED"],
    )
    sub = await service.create_subscription(create_req)
    assert sub.id.startswith("wh-")
    assert sub.name == "Slack Production Alerts"
    assert sub.channel_type == "slack"

    # 2. List Webhooks
    subs = await service.list_subscriptions()
    assert len(subs) >= 1
    assert any(s.id == sub.id for s in subs)

    # 3. Test HMAC-SHA256 Signature
    sig = WebhookService.compute_hmac_signature("secret-token-12345", b'{"test":"data"}')
    assert sig.startswith("sha256=")

    # 4. Test Delivery Ping
    ping_res = await service.test_webhook_delivery(sub.target_url, sub.secret_token)
    assert ping_res.status in ["DELIVERED", "FAILED"]
    assert ping_res.signature_header.startswith("sha256=")

    # 5. Dispatch Event
    dispatched_count = await service.dispatch_event("AUDIT_EVENT", {"action": "TEST_MUTATION"})
    assert dispatched_count >= 1

    # 6. Delete Webhook
    deleted = await service.delete_subscription(sub.id)
    assert deleted is True
    subs_after = await service.list_subscriptions()
    assert not any(s.id == sub.id for s in subs_after)
