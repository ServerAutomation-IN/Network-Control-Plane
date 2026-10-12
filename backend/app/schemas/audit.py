"""AuditEvent Pydantic Schemas — Network Control Plane"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    action: str
    actor: str
    resource_type: str
    resource_id: str
    risk_level: str
    details: dict = {}
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
