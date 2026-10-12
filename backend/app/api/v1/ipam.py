"""IPAM REST API Router — Network Control Plane"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ipam import (
    SubnetDetailSchema,
    IPAMConflictSchema,
    IPAMValidationRequest,
    IPAMValidationResponse,
)
from app.services.ipam import IPAMService

router = APIRouter(prefix="/ipam", tags=["IPAM"])


@router.get("/subnets", response_model=List[SubnetDetailSchema])
async def get_subnets_summary(db: AsyncSession = Depends(get_db)):
    """List all managed subnets with IP utilization calculations."""
    service = IPAMService(db)
    return await service.get_all_subnets_summary()


@router.get("/conflicts", response_model=List[IPAMConflictSchema])
async def get_ipam_conflicts(
    host_id: Optional[str] = Query(None, description="Optional host ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Audit and return active subnet overlaps and IP collisions."""
    service = IPAMService(db)
    return await service.detect_conflicts(host_id=host_id)


@router.post("/validate", response_model=IPAMValidationResponse, status_code=status.HTTP_200_OK)
async def validate_ip_allocation(
    payload: IPAMValidationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate CIDR subnet boundaries and static IP availability."""
    service = IPAMService(db)
    return service.validate_allocation(payload)
