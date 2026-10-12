"""Integration Tests for Cloud Event-Driven Ingestion Webhooks — Network Control Plane"""

import base64
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import get_db
from app.models.audit import AuditEvent
from app.schemas.host import HostCreate
from app.services.inventory import InventoryService


@pytest.mark.asyncio
async def test_azure_event_grid_validation_handshake(db_session):
    """Test Azure Event Grid subscription validation handshake returns validationResponse."""
    app.dependency_overrides[get_db] = lambda: db_session

    azure_handshake_payload = [
        {
            "id": "2d1781af-3a4c-4d7c-bd0c-e34b19da4e66",
            "topic": "/subscriptions/sub-1234/resourceGroups/rg-prod/providers/Microsoft.EventGrid/topics/ncp-topic",
            "subject": "",
            "data": {
                "validationCode": "514838BB-4360-4663-9C09-5CEFBEE8526B",
                "validationUrl": "https://rp-eastus.eventgrid.azure.net:443/eventgrid/api/validate",
            },
            "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
            "eventTime": "2026-10-12T10:00:00.0000000Z",
            "dataVersion": "2",
        }
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/azure", json=azure_handshake_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["validationResponse"] == "514838BB-4360-4663-9C09-5CEFBEE8526B"


@pytest.mark.asyncio
async def test_aws_sns_subscription_confirmation_handshake(db_session):
    """Test AWS SNS SubscriptionConfirmation handshake returns handshake_accepted."""
    app.dependency_overrides[get_db] = lambda: db_session

    aws_sns_payload = {
        "Type": "SubscriptionConfirmation",
        "MessageId": "165545c6-65c4-42a4-808b-aa975845d734",
        "Token": "2336412f37fb687f5d51e6e241d09c805a5a57b32187",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:ncp-vpc-events",
        "Message": "You have chosen to subscribe to the topic arn:aws:sns:us-east-1:123456789012:ncp-vpc-events",
        "SubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription&TopicArn=...",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/aws", json=aws_sns_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "handshake_accepted"
    assert data["provider"] == "aws"
    assert data["action_taken"] == "VALIDATION_HANDSHAKE"
    assert "arn:aws:sns:us-east-1:123456789012:ncp-vpc-events" in data["message"]


@pytest.mark.asyncio
async def test_aws_eventbridge_event_ingestion_and_host_sync(db_session):
    """Test AWS EventBridge event ingestion triggers delta sync and logs audit record."""
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Register AWS host
    inv_service = InventoryService(db_session)
    await inv_service.register_host(
        HostCreate(
            name="AWS Production US-East",
            endpoint="us-east-1",
            provider_type="aws",
            environment="production",
        )
    )

    # 2. Ingest AWS CloudTrail / EventBridge CreateSubnet event
    eventbridge_payload = {
        "version": "0",
        "id": "6a7e8dda-dd1d-4f0e-b443-32e11a4a69cb",
        "detail-type": "AWS API Call via CloudTrail",
        "source": "aws.ec2",
        "detail": {
            "eventName": "CreateSubnet",
            "requestParameters": {
                "vpcId": "vpc-0a1b2c3d4e5f67890",
                "cidrBlock": "10.0.3.0/24",
            },
            "responseElements": {
                "subnet": {
                    "subnetId": "subnet-0123456789abcdef0",
                }
            },
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/aws", json=eventbridge_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["provider"] == "aws"
    assert data["action_taken"] == "DELTA_SYNC_EXECUTED"
    assert data["synced_host_id"] == "host-aws-production-us-east"

    # 3. Verify Audit Event was recorded
    audit_stmt = select(AuditEvent).where(
        AuditEvent.action == "CLOUD_WEBHOOK_INGESTION_AWS",
        AuditEvent.resource_id == "host-aws-production-us-east",
    )
    audit_record = (await db_session.execute(audit_stmt)).scalars().first()
    assert audit_record is not None
    assert audit_record.details.get("event_type") == "CreateSubnet"


@pytest.mark.asyncio
async def test_gcp_pubsub_event_ingestion(db_session):
    """Test GCP Cloud Pub/Sub base64 event decoding, ingestion, and host sync."""
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Register GCP host
    inv_service = InventoryService(db_session)
    await inv_service.register_host(
        HostCreate(
            name="GCP Prod Project",
            endpoint="gcp-prod-123",
            provider_type="gcp",
            environment="production",
        )
    )

    # 2. Encode mock GCP Pub/Sub message data
    inner_data = {
        "protoPayload": {
            "methodName": "compute.subnetworks.insert",
            "resourceName": "projects/gcp-prod-123/regions/us-central1/subnetworks/subnet-k8s",
        }
    }
    b64_data = base64.b64encode(json.dumps(inner_data).encode("utf-8")).decode("utf-8")

    pubsub_payload = {
        "message": {
            "data": b64_data,
            "messageId": "msg-gcp-123456",
            "publishTime": "2026-10-12T10:05:00.000Z",
        }
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/gcp", json=pubsub_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["provider"] == "gcp"
    assert data["event_type"] == "compute.subnetworks.insert"
    assert data["action_taken"] == "DELTA_SYNC_EXECUTED"
    assert data["synced_host_id"] == "host-gcp-prod-project"


@pytest.mark.asyncio
async def test_vmware_vsphere_event_ingestion(db_session):
    """Test VMware vSphere network event ingestion and delta sync."""
    app.dependency_overrides[get_db] = lambda: db_session

    # 1. Register VMware host
    inv_service = InventoryService(db_session)
    await inv_service.register_host(
        HostCreate(
            name="vCenter Datacenter 1",
            endpoint="vc-dc1.internal",
            provider_type="vmware",
            environment="production",
        )
    )

    vmware_payload = {
        "topic": "com.vmware.vcenter.network.portgroup.created",
        "portgroup_name": "dvPortGroup-App-VLAN20",
        "dvs_name": "vDS-Core",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/vmware", json=vmware_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["provider"] == "vmware"
    assert data["action_taken"] == "DELTA_SYNC_EXECUTED"
    assert data["synced_host_id"] == "host-vcenter-datacenter-1"


@pytest.mark.asyncio
async def test_unsupported_cloud_provider_rejected(db_session):
    """Test ingestion endpoint rejects unknown or unsupported cloud providers."""
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/webhooks/cloud/unknown_cloud", json={"test": 123})

    assert response.status_code == 400
    assert "Unsupported cloud provider" in response.json()["detail"]
