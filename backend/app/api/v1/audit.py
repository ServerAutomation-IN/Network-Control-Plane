"""Audit Events API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=List[AuditEventResponse])
async def list_audit_events(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List immutable audit log records for network operations."""
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [AuditEventResponse.model_validate(e) for e in events]
