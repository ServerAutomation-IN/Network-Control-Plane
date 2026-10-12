"""Topology API Router — Network Control Plane"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.topology import TopologyResponse
from app.services.topology import TopologyService

router = APIRouter(prefix="/topology", tags=["Topology"])


@router.get("", response_model=TopologyResponse)
async def get_topology(
    host_id: str | None = Query(None, description="Optional host ID filter"),
    environment: str | None = Query(None, description="Optional environment filter"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve normalized node/edge topology graph payload for visualization."""
    service = TopologyService(db)
    return await service.get_topology_graph(host_id=host_id, environment=environment)
