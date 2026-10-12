"""Outbound Webhooks & Alerting REST API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import CurrentUser, UserRole, require_role
from app.schemas.webhook import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookTestRequest,
    WebhookTestResponse,
)
from app.services.webhook import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Outbound Webhooks & Alerting Engine"])


@router.get("", response_model=List[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """List all registered webhook subscriptions."""
    service = WebhookService(db)
    return await service.list_subscriptions()


@router.post("", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
):
    """Register a new outbound webhook channel (Slack, PagerDuty, MS Teams, Generic)."""
    service = WebhookService(db)
    return await service.create_subscription(payload)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a webhook subscription channel."""
    service = WebhookService(db)
    deleted = await service.delete_subscription(subscription_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook subscription '{subscription_id}' not found.",
        )


@router.post("/test-ping", response_model=WebhookTestResponse)
async def test_webhook_ping(
    payload: WebhookTestRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Execute real-time test delivery ping to specified HTTP endpoint with HMAC signature."""
    service = WebhookService(db)
    return await service.test_webhook_delivery(payload.target_url, payload.secret_token)


@router.post("/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_existing_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])),
):
    """Execute real-time test delivery ping for registered webhook subscription."""
    service = WebhookService(db)
    subs = await service.list_subscriptions()
    matching = [s for s in subs if s.id == subscription_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook subscription '{subscription_id}' not found.",
        )
    sub = matching[0]
    return await service.test_webhook_delivery(sub.target_url, sub.secret_token)
