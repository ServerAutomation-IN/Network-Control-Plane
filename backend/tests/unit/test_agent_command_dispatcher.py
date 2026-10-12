"""Unit Tests for AgentCommandDispatcher Service — Network Control Plane"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentCommandResult
from app.services.agent_dispatcher import AgentCommandDispatcher


@pytest.mark.asyncio
async def test_agent_dispatcher_enqueue_and_fetch(db_session: AsyncSession):
    """Test enqueuing commands for a host transitions them to PENDING and then DISPATCHED on fetch."""
    dispatcher = AgentCommandDispatcher(db_session)

    # 1. Enqueue command
    cmd = await dispatcher.enqueue_command(
        host_id="host-test-agent-01",
        action="CREATE_NETWORK",
        payload={"name": "test_net", "driver": "bridge"},
    )
    assert cmd.id.startswith("cmd-")
    assert cmd.host_id == "host-test-agent-01"
    assert cmd.action == "CREATE_NETWORK"
    assert cmd.status == "PENDING"

    # 2. Fetch pending commands
    pending = await dispatcher.get_pending_commands("host-test-agent-01")
    assert len(pending) == 1
    assert pending[0].id == cmd.id
    assert pending[0].status == "DISPATCHED"
    assert pending[0].dispatched_at is not None

    # 3. Fetching again returns empty list since status is no longer PENDING
    pending_empty = await dispatcher.get_pending_commands("host-test-agent-01")
    assert len(pending_empty) == 0


@pytest.mark.asyncio
async def test_agent_dispatcher_record_success_result(db_session: AsyncSession):
    """Test recording a successful execution result updates status to COMPLETED."""
    dispatcher = AgentCommandDispatcher(db_session)

    cmd = await dispatcher.enqueue_command(
        host_id="host-test-agent-02",
        action="ATTACH_ENDPOINT",
        payload={"network_ref_id": "net-1", "container_ref_id": "cnt-1"},
    )

    result_payload = AgentCommandResult(
        command_id=cmd.id,
        host_id=cmd.host_id,
        success=True,
        result_data={"attached": True, "ip_address": "172.20.0.10"},
    )

    updated_cmd = await dispatcher.record_command_result(cmd.id, result_payload)
    assert updated_cmd.status == "COMPLETED"
    assert updated_cmd.result["attached"] is True
    assert updated_cmd.completed_at is not None
    assert updated_cmd.error_message is None


@pytest.mark.asyncio
async def test_agent_dispatcher_record_failure_result(db_session: AsyncSession):
    """Test recording a failed execution result updates status to FAILED with error message."""
    dispatcher = AgentCommandDispatcher(db_session)

    cmd = await dispatcher.enqueue_command(
        host_id="host-test-agent-03",
        action="DELETE_NETWORK",
        payload={"network_ref_id": "net-protected"},
    )

    result_payload = AgentCommandResult(
        command_id=cmd.id,
        host_id=cmd.host_id,
        success=False,
        error_message="Network is active and currently has active endpoints attached",
    )

    updated_cmd = await dispatcher.record_command_result(cmd.id, result_payload)
    assert updated_cmd.status == "FAILED"
    assert updated_cmd.error_message == "Network is active and currently has active endpoints attached"
    assert updated_cmd.completed_at is not None
