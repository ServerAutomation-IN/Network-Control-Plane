"""Cloud Event-Driven Ingestion Webhooks API Router — Network Control Plane"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.cloud_webhook import CloudWebhookResponse, AzureValidationResponse
from app.services.cloud_webhook import CloudWebhookService

router = APIRouter(prefix="/webhooks/cloud", tags=["Cloud Event-Driven Webhooks"])


@router.post(
    "/{provider}",
    response_model=CloudWebhookResponse | AzureValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_cloud_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Universal ingestion gateway for cloud provider events (AWS, Azure, GCP, VMware)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    service = CloudWebhookService(db)
    try:
        headers_dict = dict(request.headers)
        return await service.process_cloud_event(
            provider=provider,
            payload=payload,
            headers=headers_dict,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


@router.post("/aws", response_model=CloudWebhookResponse, status_code=status.HTTP_200_OK)
async def ingest_aws_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ingest AWS EventBridge and SNS network lifecycle notifications."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    service = CloudWebhookService(db)
    result = await service.process_cloud_event(provider="aws", payload=payload, headers=dict(request.headers))
    if isinstance(result, CloudWebhookResponse):
        return result
    return CloudWebhookResponse(
        status="processed",
        provider="aws",
        action_taken="HANDSHAKE",
        message="AWS Event Processed",
    )


@router.post("/azure", response_model=CloudWebhookResponse | AzureValidationResponse, status_code=status.HTTP_200_OK)
async def ingest_azure_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ingest Azure Event Grid VNet and Subnet lifecycle events with validation handshake."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    service = CloudWebhookService(db)
    return await service.process_cloud_event(provider="azure", payload=payload, headers=dict(request.headers))


@router.post("/gcp", response_model=CloudWebhookResponse, status_code=status.HTTP_200_OK)
async def ingest_gcp_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ingest Google Cloud Pub/Sub VPC and Subnetwork change notifications."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    service = CloudWebhookService(db)
    result = await service.process_cloud_event(provider="gcp", payload=payload, headers=dict(request.headers))
    if isinstance(result, CloudWebhookResponse):
        return result
    return CloudWebhookResponse(
        status="processed",
        provider="gcp",
        action_taken="HANDSHAKE",
        message="GCP Event Processed",
    )


@router.post("/vmware", response_model=CloudWebhookResponse, status_code=status.HTTP_200_OK)
async def ingest_vmware_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ingest VMware vSphere Distributed Switch and PortGroup events."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    service = CloudWebhookService(db)
    result = await service.process_cloud_event(provider="vmware", payload=payload, headers=dict(request.headers))
    if isinstance(result, CloudWebhookResponse):
        return result
    return CloudWebhookResponse(
        status="processed",
        provider="vmware",
        action_taken="HANDSHAKE",
        message="VMware Event Processed",
    )
