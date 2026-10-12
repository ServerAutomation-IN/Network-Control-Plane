"""Audit Logging Service — Network Control Plane

Records immutable audit events for all mutating network operations.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent


class AuditService:
    """Service for logging immutable audit events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor: str = "system",
        risk_level: str = "LOW",
        details: dict | None = None,
    ) -> AuditEvent:
        """Create and persist an immutable audit event log entry."""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(event)
        await self.db.flush()

        # Trigger Webhook Event Dispatcher for non-routine / high risk audit events
        if action != "AGENT_SNAPSHOT_INGEST":
            try:
                from app.services.webhook import WebhookService
                await WebhookService(self.db).dispatch_event(
                    event_type=action,
                    details={
                        "action": action,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "actor": actor,
                        "risk_level": risk_level,
                        "details": details or {},
                    },
                )
            except Exception:
                pass

        return event
