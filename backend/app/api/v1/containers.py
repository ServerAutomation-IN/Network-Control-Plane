"""Containers API Router — Network Control Plane"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.container import Container
from app.schemas.container import ContainerResponse, ContainerAttachmentSchema

router = APIRouter(prefix="/containers", tags=["Containers"])


@router.get("", response_model=List[ContainerResponse])
async def list_containers(db: AsyncSession = Depends(get_db)):
    """List all workload containers across managed hosts."""
    stmt = select(Container).options(
        selectinload(Container.network_attachments).selectinload(Container.network_attachments.property.mapper.class_.network)
    )
    result = await db.execute(stmt)
    containers = result.scalars().all()

    response_data = []
    for cnt in containers:
        attachments = []
        for att in cnt.network_attachments:
            attachments.append(ContainerAttachmentSchema(
                network_id=att.network_id,
                network_name=att.network.name if att.network else None,
                ip_address=att.ip_address,
                mac_address=att.mac_address,
                aliases=att.aliases or [],
            ))

        item = ContainerResponse(
            id=cnt.id,
            host_id=cnt.host_id,
            provider_ref_id=cnt.provider_ref_id,
            name=cnt.name,
            image=cnt.image,
            status=cnt.status,
            labels=cnt.labels,
            created_at=cnt.created_at,
            attachments=attachments,
        )
        response_data.append(item)

    return response_data


@router.get("/{container_id}", response_model=ContainerResponse)
async def get_container(container_id: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific workload container."""
    stmt = select(Container).where(Container.id == container_id).options(
        selectinload(Container.network_attachments).selectinload(Container.network_attachments.property.mapper.class_.network)
    )
    result = await db.execute(stmt)
    cnt = result.scalar_one_or_none()

    if not cnt:
        raise HTTPException(status_code=404, detail=f"Container '{container_id}' not found.")

    attachments = []
    for att in cnt.network_attachments:
        attachments.append(ContainerAttachmentSchema(
            network_id=att.network_id,
            network_name=att.network.name if att.network else None,
            ip_address=att.ip_address,
            mac_address=att.mac_address,
            aliases=att.aliases or [],
        ))

    return ContainerResponse(
        id=cnt.id,
        host_id=cnt.host_id,
        provider_ref_id=cnt.provider_ref_id,
        name=cnt.name,
        image=cnt.image,
        status=cnt.status,
        labels=cnt.labels,
        created_at=cnt.created_at,
        attachments=attachments,
    )
