"""Unit Tests for Drift Detection & Reconciliation Engine — Network Control Plane"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.drift import DriftEngine
from app.schemas.drift import DriftType, ReconciliationStatus

VALID_YAML_MANIFEST = """apiVersion: network-control-plane/v1
kind: NetworkManifest
metadata:
  name: test-production-manifest
spec:
  networks:
    - name: desired_app_net
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      attachable: true
      subnets:
        - subnet: 172.30.0.0/16
          gateway: 172.30.0.1
"""


def test_parse_yaml_manifest_success():
    """Test parsing a valid network-control-plane/v1 YAML manifest."""
    manifest = DriftEngine.parse_yaml_manifest(VALID_YAML_MANIFEST)
    assert manifest.apiVersion == "network-control-plane/v1"
    assert manifest.kind == "NetworkManifest"
    assert manifest.metadata["name"] == "test-production-manifest"
    assert len(manifest.spec["networks"]) == 1
    assert manifest.spec["networks"][0].name == "desired_app_net"


def test_parse_yaml_manifest_invalid_version():
    """Test error handling when parsing invalid apiVersion manifest."""
    invalid_yaml = """apiVersion: v1
kind: ConfigMap
spec: {}
"""
    with pytest.raises(ValueError, match="Unsupported apiVersion"):
        DriftEngine.parse_yaml_manifest(invalid_yaml)


@pytest.mark.asyncio
async def test_drift_comparison(db_session: AsyncSession):
    """Test comparing desired-state YAML spec against database inventory."""
    engine = DriftEngine(db_session)
    manifest_name, drifts, actions = await engine.compare_manifest_against_runtime(VALID_YAML_MANIFEST)

    assert manifest_name == "test-production-manifest"
    assert len(drifts) >= 1
    assert len(actions) >= 1

    # Verify missing network drift detection
    missing_drifts = [d for d in drifts if d.drift_type == DriftType.MISSING_IN_RUNTIME]
    assert len(missing_drifts) == 1
    assert missing_drifts[0].resource_name == "desired_app_net"

    # Verify action creation
    create_actions = [a for a in actions if a.action_type == "CREATE_NETWORK"]
    assert len(create_actions) == 1
    assert create_actions[0].target_resource == "desired_app_net"
