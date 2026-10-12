"""Container Pydantic Schemas — Network Control Plane"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ContainerAttachmentSchema(BaseModel):
    network_id: str
    network_name: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    aliases: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class ContainerResponse(BaseModel):
    id: str
    host_id: str
    provider_ref_id: str
    name: str
    image: str | None = None
    status: str
    labels: dict = {}
    created_at: datetime
    attachments: list[ContainerAttachmentSchema] = []

    model_config = ConfigDict(from_attributes=True)
