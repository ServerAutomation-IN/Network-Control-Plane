"""Cloud Event-Driven Ingestion Webhooks Schemas — Network Control Plane"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CloudWebhookResponse(BaseModel):
    """Normalized response payload for cloud webhook event ingestion."""

    status: str = Field(..., description="Ingestion processing status (processed, handshake_accepted, ignored)")
    provider: str = Field(..., description="Cloud or hypervisor provider (aws, azure, gcp, vmware)")
    event_type: Optional[str] = Field(None, description="Extracted event type or action name")
    resource_id: Optional[str] = Field(None, description="Primary affected cloud network resource identifier")
    synced_host_id: Optional[str] = Field(None, description="Identifier of the InfrastructureHost updated by delta sync")
    action_taken: str = Field(..., description="Action taken by the control plane (DELTA_SYNC_EXECUTED, VALIDATION_HANDSHAKE, EVENT_IGNORED)")
    message: Optional[str] = Field(None, description="Descriptive status message or diagnostic details")


class AzureValidationResponse(BaseModel):
    """Response payload for Azure Event Grid subscription validation handshake."""

    validationResponse: str = Field(..., description="Echo of Azure Event Grid validationCode")
