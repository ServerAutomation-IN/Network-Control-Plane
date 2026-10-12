"""Agent Command Dispatcher Service — Network Control Plane

Manages the queuing, polling dispatch, and result reconciliation of imperative
mutation commands executed on remote host agent nodes.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_command import AgentCommand
from app.models.host import InfrastructureHost
from app.schemas.agent import AgentCommandResult
from app.services.audit import AuditService


class AgentCommandDispatcher:
    """Service governing bidirectional command execution against remote host agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue_command(
        self,
        host_id: str,
        action: str,
        payload: dict,
        timeout_seconds: int = 30,
    ) -> AgentCommand:
        """Enqueue a new imperative command targeted at a remote host agent."""
        cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        cmd = AgentCommand(
            id=cmd_id,
            host_id=host_id,
            action=action.upper(),
            status="PENDING",
            payload=payload,
            created_at=now,
        )
        self.db.add(cmd)

        await AuditService(self.db).log_event(
            action="AGENT_COMMAND_ENQUEUE",
            resource_type="agent_command",
            resource_id=cmd_id,
            risk_level="LOW",
            details={"host_id": host_id, "action": action},
        )

        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd

    async def get_pending_commands(self, host_id: str) -> List[AgentCommand]:
        """Fetch all PENDING commands for a specific host and mark them DISPATCHED."""
        stmt = (
            select(AgentCommand)
            .where(AgentCommand.host_id == host_id, AgentCommand.status == "PENDING")
            .order_by(AgentCommand.created_at.asc())
        )
        result = await self.db.execute(stmt)
        commands = list(result.scalars().all())

        if commands:
            now = datetime.now(timezone.utc)
            for cmd in commands:
                cmd.status = "DISPATCHED"
                cmd.dispatched_at = now
            await self.db.commit()

        return commands

    async def record_command_result(
        self,
        command_id: str,
        result: AgentCommandResult,
    ) -> AgentCommand:
        """Record local execution result reported back by host agent daemon."""
        stmt = select(AgentCommand).where(AgentCommand.id == command_id)
        cmd_result = await self.db.execute(stmt)
        cmd = cmd_result.scalar_one_or_none()

        if not cmd:
            raise ValueError(f"Agent command '{command_id}' not found.")

        now = datetime.now(timezone.utc)
        cmd.status = "COMPLETED" if result.success else "FAILED"
        cmd.result = result.result_data
        cmd.error_message = result.error_message
        cmd.completed_at = now

        await AuditService(self.db).log_event(
            action="AGENT_COMMAND_EXECUTE",
            resource_type="agent_command",
            resource_id=command_id,
            risk_level="LOW" if result.success else "HIGH",
            details={
                "host_id": cmd.host_id,
                "action": cmd.action,
                "success": result.success,
                "error": result.error_message,
            },
        )

        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd

    async def await_command_execution(
        self,
        command_id: str,
        timeout_seconds: float = 15.0,
        poll_interval: float = 0.25,
    ) -> AgentCommand:
        """Wait asynchronously until a command has finished executing on remote agent."""
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            stmt = select(AgentCommand).where(AgentCommand.id == command_id)
            result = await self.db.execute(stmt)
            cmd = result.scalar_one_or_none()

            if cmd and cmd.status in ("COMPLETED", "FAILED"):
                return cmd

            await asyncio.sleep(poll_interval)

        # Handle timeout
        stmt = select(AgentCommand).where(AgentCommand.id == command_id)
        result = await self.db.execute(stmt)
        cmd = result.scalar_one_or_none()
        if cmd:
            cmd.status = "TIMED_OUT"
            cmd.error_message = f"Command timed out after {timeout_seconds} seconds without agent response."
            cmd.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(cmd)
            raise TimeoutError(f"Command '{command_id}' timed out after {timeout_seconds}s.")

        raise ValueError(f"Command '{command_id}' not found.")
