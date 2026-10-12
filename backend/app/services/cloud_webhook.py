"""Cloud Event-Driven Ingestion Webhooks Service — Network Control Plane

Handles incoming cloud event notifications (AWS EventBridge, Azure Event Grid,
GCP Pub/Sub, VMware vSphere), validates subscription handshakes, resolves target
cloud infrastructure hosts, executes inventory delta synchronizations, and logs
immutable audit events.
"""

import base64
import json
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.schemas.cloud_webhook import CloudWebhookResponse, AzureValidationResponse
from app.services.inventory import InventoryService
from app.services.audit import AuditService
from app.services.webhook import WebhookService


class CloudWebhookService:
    """Service orchestrating incoming cloud provider event ingestion and state sync."""

    SUPPORTED_PROVIDERS = {"aws", "azure", "gcp", "vmware", "vsphere"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_cloud_event(
        self,
        provider: str,
        payload: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> CloudWebhookResponse | AzureValidationResponse:
        """Process incoming webhook notification from supported cloud providers.

        Args:
            provider: Cloud provider name ('aws', 'azure', 'gcp', 'vmware').
            payload: Raw event payload dictionary or array.
            headers: Optional HTTP headers received with the request.
        """
        norm_provider = provider.lower()
        if norm_provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported cloud provider '{provider}'. "
                f"Supported providers: {', '.join(sorted(self.SUPPORTED_PROVIDERS))}."
            )

        if norm_provider == "vsphere":
            norm_provider = "vmware"

        # 1. Provider-specific handshake and parsing
        if norm_provider == "azure":
            azure_handshake = self._handle_azure_handshake(payload)
            if azure_handshake:
                return azure_handshake
            event_type, resource_id, event_details = self._parse_azure_event(payload)

        elif norm_provider == "aws":
            aws_handshake = self._handle_aws_handshake(payload)
            if aws_handshake:
                return aws_handshake
            event_type, resource_id, event_details = self._parse_aws_event(payload)

        elif norm_provider == "gcp":
            event_type, resource_id, event_details = self._parse_gcp_event(payload)

        elif norm_provider == "vmware":
            event_type, resource_id, event_details = self._parse_vmware_event(payload)

        else:
            event_type, resource_id, event_details = "UNKNOWN", None, {}

        # 2. Resolve matching InfrastructureHost in PostgreSQL
        stmt = select(InfrastructureHost).where(InfrastructureHost.provider_type == norm_provider)
        host = (await self.db.execute(stmt)).scalars().first()

        synced_host_id = None
        action_taken = "EVENT_RECORDED"

        if host:
            synced_host_id = host.id
            # 3. Trigger inventory delta synchronization on the target host
            inventory_service = InventoryService(self.db)
            try:
                await inventory_service.sync_host(host_id=host.id, endpoint=host.endpoint)
                action_taken = "DELTA_SYNC_EXECUTED"
            except Exception as sync_exc:
                action_taken = f"DELTA_SYNC_FAILED: {sync_exc!s}"

            # 4. Audit Log & Outbound notification
            await AuditService(self.db).log_event(
                action=f"CLOUD_WEBHOOK_INGESTION_{norm_provider.upper()}",
                resource_type="host",
                resource_id=host.id,
                risk_level="LOW",
                details={
                    "provider": norm_provider,
                    "event_type": event_type,
                    "resource_id": resource_id,
                    "action_taken": action_taken,
                    "event_details": event_details,
                },
            )
            await WebhookService(self.db).dispatch_event(
                event_type="CLOUD_EVENT_INGESTED",
                details={
                    "provider": norm_provider,
                    "host_id": host.id,
                    "event_type": event_type,
                    "resource_id": resource_id,
                },
            )
        else:
            action_taken = "NO_MATCHING_HOST"
            await AuditService(self.db).log_event(
                action=f"CLOUD_WEBHOOK_RECEIVED_{norm_provider.upper()}",
                resource_type="cloud_event",
                resource_id=resource_id or norm_provider,
                risk_level="LOW",
                details={
                    "provider": norm_provider,
                    "event_type": event_type,
                    "resource_id": resource_id,
                    "note": f"No active host with provider_type='{norm_provider}' was registered.",
                },
            )

        return CloudWebhookResponse(
            status="processed",
            provider=norm_provider,
            event_type=event_type,
            resource_id=resource_id,
            synced_host_id=synced_host_id,
            action_taken=action_taken,
            message=f"Successfully processed {norm_provider.upper()} event '{event_type}'.",
        )

    # --------------------------------------------------------------------------
    # Handshake & Parsing Helpers
    # --------------------------------------------------------------------------

    def _handle_azure_handshake(self, payload: Any) -> Optional[AzureValidationResponse]:
        """Check and respond to Azure Event Grid subscription validation handshake."""
        events = payload if isinstance(payload, list) else [payload]
        for ev in events:
            if not isinstance(ev, dict):
                continue
            if ev.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
                validation_code = ev.get("data", {}).get("validationCode")
                if validation_code:
                    return AzureValidationResponse(validationResponse=str(validation_code))
        return None

    def _parse_azure_event(self, payload: Any) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Extract event type and resource URI from Azure Event Grid payload."""
        events = payload if isinstance(payload, list) else [payload]
        first_event = events[0] if events and isinstance(events[0], dict) else {}
        event_type = first_event.get("eventType", "Microsoft.Network.Event")
        resource_id = first_event.get("subject") or first_event.get("data", {}).get("resourceUri")
        return event_type, resource_id, first_event

    def _handle_aws_handshake(self, payload: Any) -> Optional[CloudWebhookResponse]:
        """Check and acknowledge AWS SNS SubscriptionConfirmation handshake."""
        if isinstance(payload, dict) and payload.get("Type") == "SubscriptionConfirmation":
            topic_arn = payload.get("TopicArn", "arn:aws:sns:unknown")
            return CloudWebhookResponse(
                status="handshake_accepted",
                provider="aws",
                event_type="SubscriptionConfirmation",
                resource_id=topic_arn,
                synced_host_id=None,
                action_taken="VALIDATION_HANDSHAKE",
                message=f"AWS SNS subscription handshake acknowledged for topic '{topic_arn}'.",
            )
        return None

    def _parse_aws_event(self, payload: Any) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Extract event name and resource ID from AWS EventBridge / CloudWatch event."""
        if not isinstance(payload, dict):
            return "aws.unknown", None, {}

        # 1. AWS SNS wrapper around EventBridge
        if payload.get("Type") == "Notification" and "Message" in payload:
            try:
                inner_payload = json.loads(payload["Message"])
                if isinstance(inner_payload, dict):
                    payload = inner_payload
            except Exception:
                pass

        event_type = payload.get("detail", {}).get("eventName") or payload.get("detail-type") or "aws.event"
        detail = payload.get("detail", {})

        # Extract affected resource ID (Subnet, VPC, ENI)
        resource_id = None
        if payload.get("resources") and len(payload["resources"]) > 0:
            resource_id = payload["resources"][0]
        elif isinstance(detail, dict):
            req_params = detail.get("requestParameters", {})
            resp_elems = detail.get("responseElements", {})
            resource_id = (
                req_params.get("subnetId")
                or req_params.get("vpcId")
                or req_params.get("networkInterfaceId")
                or resp_elems.get("subnet", {}).get("subnetId")
                or resp_elems.get("vpc", {}).get("vpcId")
            )

        return event_type, resource_id, detail

    def _parse_gcp_event(self, payload: Any) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Extract event and resource from GCP Cloud Pub/Sub push notification."""
        if not isinstance(payload, dict):
            return "gcp.unknown", None, {}

        msg = payload.get("message", {})
        data_str = msg.get("data")
        parsed_data = {}
        if data_str:
            try:
                decoded = base64.b64decode(data_str).decode("utf-8")
                parsed_data = json.loads(decoded)
            except Exception:
                parsed_data = {"raw": data_str}

        event_type = (
            msg.get("attributes", {}).get("eventType")
            or parsed_data.get("protoPayload", {}).get("methodName")
            or "gcp.pubsub.message"
        )
        resource_id = (
            parsed_data.get("protoPayload", {}).get("resourceName")
            or parsed_data.get("resource", {}).get("labels", {}).get("subnetwork_id")
            or msg.get("messageId")
        )

        return event_type, resource_id, parsed_data

    def _parse_vmware_event(self, payload: Any) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Extract event topic and portgroup/vswitch ID from VMware vSphere webhook."""
        if not isinstance(payload, dict):
            return "vmware.unknown", None, {}

        event_type = payload.get("topic") or payload.get("eventType") or "vsphere.network.event"
        resource_id = (
            payload.get("dvs_name")
            or payload.get("portgroup_name")
            or payload.get("vm_id")
            or payload.get("id")
        )
        return event_type, resource_id, payload
