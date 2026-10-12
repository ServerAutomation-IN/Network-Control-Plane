"""Unit Tests for AWS VPC Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.aws.adapter import AWSAdapter


@pytest.mark.asyncio
async def test_aws_adapter_discovery():
    """Test AWSAdapter discovery of AWS VPC networks and EC2 ENI workloads."""
    adapter = AWSAdapter(region_name="us-east-1")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "aws"
    assert snapshot["endpoint"] == "us-east-1"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "aws-prod-vpc"
    assert networks[0]["driver"] == "aws-vpc"
    assert len(networks[0]["subnets"]) >= 1

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "aws-ec2-api-server"
    assert "instance_type" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_aws_adapter_mutations():
    """Test AWSAdapter network lifecycle and ENI attachment operations."""
    adapter = AWSAdapter()

    spec = {"name": "aws-dev-vpc", "driver": "aws-vpc"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "aws-dev-vpc"
    assert created_net["provider_ref_id"] == "vpc-aws-dev-vpc"

    assert await adapter.connect_container("vpc-0a1b2c3d4e5f67890", "eni-0123456789abcdef0") is True
    assert await adapter.disconnect_container("vpc-0a1b2c3d4e5f67890", "eni-0123456789abcdef0") is True
    assert await adapter.delete_network("vpc-0a1b2c3d4e5f67890") is True
