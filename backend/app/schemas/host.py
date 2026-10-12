"""InfrastructureHost Pydantic Schemas — Network Control Plane"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HostBase(BaseModel):
    name: str
    endpoint: str
    provider_type: str = "docker"
    environment: str = "development"


class HostCreate(HostBase):
    tls_cert: str | None = None
    encrypted_tls_cert: str | None = None


class HostResponse(HostBase):
    id: str
    status: str
    docker_version: str | None = None
    os: str | None = None
    architecture: str | None = None
    has_tls_cert: bool = False
    last_seen: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BootstrapTokenCreate(BaseModel):
    host_name_hint: str | None = None
    environment: str = "production"
    provider_type: str = "docker"


class BootstrapTokenResponse(BaseModel):
    token: str
    expires_in: int
    expires_at: datetime
    control_plane_url: str
    commands: dict[str, str]


class BootstrapStatusResponse(BaseModel):
    token: str
    status: str  # WAITING | ONLINE | EXPIRED
    is_used: bool = False
    host: HostResponse | None = None

