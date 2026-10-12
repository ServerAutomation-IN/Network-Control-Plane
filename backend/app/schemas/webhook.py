"""Webhook Schemas — Network Control Plane"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class WebhookSubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Friendly subscription name")
    channel_type: str = Field("generic", description="Channel type: slack, pagerduty, msteams, generic")
    target_url: str = Field(..., description="Destination HTTP endpoint URL")
    secret_token: Optional[str] = Field(None, description="Optional secret key for HMAC-SHA256 signature verification")
    subscribed_events: List[str] = Field(default_factory=lambda: ["*"], description="Subscribed event types")
    enabled: bool = Field(True, description="Enable or disable webhook channel")


class WebhookSubscriptionResponse(BaseModel):
    id: str
    name: str
    channel_type: str
    target_url: str
    subscribed_events: List[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookTestRequest(BaseModel):
    target_url: str = Field(..., description="Target HTTP endpoint URL to test")
    secret_token: Optional[str] = Field(None, description="Secret token for HMAC-SHA256 signature verification")


class WebhookTestResponse(BaseModel):
    status: str  # DELIVERED, FAILED
    status_code: int
    latency_ms: float
    message: str
    signature_header: str


class WebhookPayload(BaseModel):
    event_type: str
    timestamp: str
    details: Dict[str, Any]
