"""Unit Tests for Pre-Deletion Safety Analysis Engine — Network Control Plane"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network import Network
from app.services.safety import PreDeletionSafetyEngine


@pytest.mark.asyncio
async def test_safety_engine_system_network(db_session: AsyncSession):
    """Verify built-in system networks return CRITICAL risk and false is_safe_to_delete flag."""
    net = Network(
        id="sys-bridge-id",
        host_id="host-1",
        provider_ref_id="raw-bridge-id",
        name="bridge",
        driver="bridge",
        scope="local",
        internal=False,
        attachable=False,
        ingress=False,
        labels={},
        options={},
    )
    db_session.add(net)
    await db_session.commit()

    engine = PreDeletionSafetyEngine(db_session)
    result = await engine.evaluate_network_deletion("sys-bridge-id")

    assert result.network_name == "bridge"
    assert result.risk_level == "CRITICAL"
    assert result.is_safe_to_delete is False
    assert any("core system" in rf for rf in result.risk_factors)


@pytest.mark.asyncio
async def test_safety_engine_empty_custom_network(db_session: AsyncSession):
    """Verify empty custom networks return LOW risk and true is_safe_to_delete flag."""
    net = Network(
        id="custom-net-id",
        host_id="host-1",
        provider_ref_id="raw-custom-id",
        name="isolated_net",
        driver="bridge",
        scope="local",
        internal=True,
        attachable=True,
        ingress=False,
        labels={},
        options={},
    )
    db_session.add(net)
    await db_session.commit()

    engine = PreDeletionSafetyEngine(db_session)
    result = await engine.evaluate_network_deletion("custom-net-id")

    assert result.network_name == "isolated_net"
    assert result.risk_level == "LOW"
    assert result.is_safe_to_delete is True
    assert result.attached_containers_count == 0
