"""Job Pydantic Schemas — Network Control Plane"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: str
    action: str
    status: str
    target_resource_id: str | None = None
    payload: dict = {}
    result: dict | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
