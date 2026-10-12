"""Remote Host Agent Protocol Router — Network Control Plane

Handles incoming HTTPS/REST requests from remote network-control-plane-agent daemons.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.host import InfrastructureHost
from app.models.bootstrap_token import BootstrapToken
from app.schemas.agent import (
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentInventorySnapshot,
    AgentEventMessage,
    AgentCommandEnvelope,
    AgentCommandResult,
    AgentResponseEnvelope,
    AgentEnrollRequest,
    AgentEnrollResponse,
)
from app.services.inventory import InventoryService
from app.services.audit import AuditService
from app.services.agent_dispatcher import AgentCommandDispatcher

router = APIRouter(prefix="/agent", tags=["Agent Protocol"])



async def verify_agent_auth(authorization: str | None = Header(None)):
    """Verify Bearer API Token for Agent Protocol endpoints if AGENT_API_TOKEN is set."""
    if not settings.AGENT_API_TOKEN:
        return True
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent authorization token missing.",
        )
    token = authorization.replace("Bearer ", "").strip()
    if token != settings.AGENT_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent authorization token.",
        )
    return True


@router.get("/health")
async def agent_health_check():
    """Agent protocol connectivity probe."""
    return {"status": "ok", "service": "network-control-plane-agent-protocol"}


@router.post("/enroll", response_model=AgentEnrollResponse)
async def enroll_agent_host(
    payload: AgentEnrollRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Enroll a remote edge host agent using a one-time bootstrap token."""
    stmt = select(BootstrapToken).where(BootstrapToken.id == payload.bootstrap_token)
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unrecognized bootstrap token.",
        )

    now = datetime.now(timezone.utc)
    if token_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bootstrap token has already been consumed and cannot be reused.",
        )

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bootstrap token has expired. Please request a new token from the control plane.",
        )


    # Generate or determine persistent host ID
    host_id = f"host-{uuid.uuid4().hex[:8]}"
    host_name = payload.hostname or token_record.host_name_hint or f"Host-{host_id}"

    host = InfrastructureHost(
        id=host_id,
        name=host_name,
        endpoint="agent://remote",
        provider_type=payload.provider_type or "docker",
        environment=payload.environment or "production",
        status="ONLINE",
        os=payload.os,
        architecture=payload.architecture,
        last_seen=now,
        created_at=now,
    )
    db.add(host)

    # Mark bootstrap token as used
    token_record.is_used = True
    token_record.used_at = now
    token_record.assigned_host_id = host_id

    # Log Audit Event
    audit_service = AuditService(db)
    await audit_service.log_event(
        action="HOST_ENROLLED",
        resource_type="host",
        resource_id=host_id,
        actor=f"bootstrap:{token_record.created_by}",
        risk_level="INFO",
        details={"hostname": host_name, "token_prefix": payload.bootstrap_token[:12]},
    )

    await db.commit()


    base_url = str(request.base_url).rstrip("/")
    persistent_api_token = settings.AGENT_API_TOKEN or f"agent_tok_{uuid.uuid4().hex}"

    return AgentEnrollResponse(
        host_id=host_id,
        api_token=persistent_api_token,
        control_plane_url=base_url,
        status="ENROLLED",
        message=f"Host '{host_name}' ({host_id}) successfully enrolled into Network Control Plane.",
    )


@router.post("/heartbeat", response_model=AgentHeartbeatResponse, dependencies=[Depends(verify_agent_auth)])

async def process_agent_heartbeat(
    payload: AgentHeartbeatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Receive and record periodic heartbeat ping from remote host agent."""
    stmt = select(InfrastructureHost).where(InfrastructureHost.id == payload.host_id)
    result = await db.execute(stmt)
    host = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if host:
        host.status = payload.status
        host.last_seen = now
        await db.commit()
    else:
        # Auto-register unknown host on heartbeat
        host = InfrastructureHost(
            id=payload.host_id,
            name=f"Agent Host ({payload.host_id})",
            endpoint="agent://remote",
            provider_type="docker",
            environment="production",
            status=payload.status,
            last_seen=now,
            created_at=now,
        )
        db.add(host)
        await db.commit()

    return AgentHeartbeatResponse(acknowledged=True, server_time=now, next_heartbeat_interval_seconds=15)


@router.post("/snapshot", response_model=AgentResponseEnvelope[Dict[str, str]], dependencies=[Depends(verify_agent_auth)])
async def process_agent_snapshot(
    payload: AgentInventorySnapshot,
    db: AsyncSession = Depends(get_db),
):
    """Ingest inventory snapshot pushed by remote host agent daemon."""
    service = InventoryService(db)
    
    # Process host details and sync inventory snapshot
    stmt = select(InfrastructureHost).where(InfrastructureHost.id == payload.host_id)
    result = await db.execute(stmt)
    host = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not host:
        host = InfrastructureHost(
            id=payload.host_id,
            name=payload.host_info.hostname or f"Host-{payload.host_id}",
            endpoint="agent://remote",
            provider_type=payload.host_info.provider_type,
            environment=payload.host_info.environment,
            status="ONLINE",
            docker_version=payload.host_info.docker_version,
            os=payload.host_info.os,
            architecture=payload.host_info.architecture,
            last_seen=now,
            created_at=now,
        )
        db.add(host)
        await db.flush()
    else:
        host.status = "ONLINE"
        host.docker_version = payload.host_info.docker_version
        host.os = payload.host_info.os
        host.architecture = payload.host_info.architecture
        host.last_seen = now
        await db.flush()

    # Synchronize networks and containers from agent snapshot into DB
    import uuid
    from sqlalchemy import delete
    from app.models.network import Network, NetworkSubnet
    from app.models.container import Container, ContainerNetwork

    net_map = {}
    existing_nets = (await db.execute(select(Network).where(Network.host_id == payload.host_id))).scalars().all()
    existing_net_map = {n.provider_ref_id: n for n in existing_nets}

    for net_data in payload.networks:
        pref_id = net_data.provider_ref_id
        if pref_id in existing_net_map:
            net_entity = existing_net_map[pref_id]
            net_entity.name = net_data.name
            net_entity.driver = net_data.driver
            net_entity.scope = net_data.scope
            net_entity.internal = net_data.internal
            net_entity.attachable = net_data.attachable
            net_entity.ingress = net_data.ingress
            net_entity.labels = net_data.labels
            net_entity.options = net_data.options
        else:
            net_entity = Network(
                id=str(uuid.uuid4()),
                host_id=payload.host_id,
                provider_ref_id=pref_id,
                name=net_data.name,
                driver=net_data.driver,
                scope=net_data.scope,
                internal=net_data.internal,
                attachable=net_data.attachable,
                ingress=net_data.ingress,
                labels=net_data.labels,
                options=net_data.options,
            )
            db.add(net_entity)

        await db.flush()
        net_map[net_data.name] = net_entity
        net_map[pref_id] = net_entity

        await db.execute(delete(NetworkSubnet).where(NetworkSubnet.network_id == net_entity.id))
        for sub in net_data.subnets:
            db.add(NetworkSubnet(
                id=str(uuid.uuid4()),
                network_id=net_entity.id,
                subnet=sub.subnet,
                gateway=sub.gateway,
                ip_range=sub.ip_range,
            ))

    existing_cnts = (await db.execute(select(Container).where(Container.host_id == payload.host_id))).scalars().all()
    existing_cnt_map = {c.provider_ref_id: c for c in existing_cnts}

    for cnt_data in payload.containers:
        pref_id = cnt_data.provider_ref_id
        if pref_id in existing_cnt_map:
            cnt_entity = existing_cnt_map[pref_id]
            cnt_entity.name = cnt_data.name
            cnt_entity.image = cnt_data.image
            cnt_entity.status = cnt_data.status
            cnt_entity.labels = cnt_data.labels
        else:
            cnt_entity = Container(
                id=str(uuid.uuid4()),
                host_id=payload.host_id,
                provider_ref_id=pref_id,
                name=cnt_data.name,
                image=cnt_data.image,
                status=cnt_data.status,
                labels=cnt_data.labels,
            )
            db.add(cnt_entity)

        await db.flush()
        await db.execute(delete(ContainerNetwork).where(ContainerNetwork.container_id == cnt_entity.id))
        for att in cnt_data.attachments:
            target_net = net_map.get(att.network_ref_id) or net_map.get(att.network_name)
            if target_net:
                db.add(ContainerNetwork(
                    id=str(uuid.uuid4()),
                    container_id=cnt_entity.id,
                    network_id=target_net.id,
                    ip_address=att.ip_address,
                    ipv6_address=att.ipv6_address,
                    mac_address=att.mac_address,
                    aliases=att.aliases,
                ))

    await AuditService(db).log_event(
        action="AGENT_SNAPSHOT_INGEST",
        resource_type="host",
        resource_id=payload.host_id,
        risk_level="LOW",
        details={
            "networks_count": len(payload.networks),
            "containers_count": len(payload.containers),
        },
    )

    await db.commit()
    return AgentResponseEnvelope(
        status="success",
        message=f"Snapshot ingested successfully for host '{payload.host_id}'",
        data={"host_id": payload.host_id},
    )


@router.post("/events", response_model=AgentResponseEnvelope[Dict[str, str]], dependencies=[Depends(verify_agent_auth)])
async def process_agent_event(
    payload: AgentEventMessage,
    db: AsyncSession = Depends(get_db),
):
    """Process real-time engine runtime event emitted by agent daemon."""
    await AuditService(db).log_event(
        action=f"AGENT_EVENT_{payload.event_type.upper().replace('.', '_')}",
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        risk_level="LOW",
        details=payload.attributes,
    )
    return AgentResponseEnvelope(
        status="success",
        message="Event received and logged",
        data={"event_type": payload.event_type, "host_id": payload.host_id},
    )


@router.post("/commands", response_model=AgentResponseEnvelope[AgentCommandEnvelope], dependencies=[Depends(verify_agent_auth)])
async def enqueue_agent_command(
    payload: AgentCommandEnvelope,
    db: AsyncSession = Depends(get_db),
):
    """Enqueue an imperative mutation command targeted at a remote host agent."""
    if not payload.host_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="host_id is required.")
    dispatcher = AgentCommandDispatcher(db)
    cmd = await dispatcher.enqueue_command(
        host_id=payload.host_id,
        action=payload.action,
        payload=payload.payload,
        timeout_seconds=payload.timeout_seconds,
    )
    return AgentResponseEnvelope(
        status="success",
        message=f"Command '{cmd.id}' enqueued for host '{cmd.host_id}'",
        data=AgentCommandEnvelope(
            command_id=cmd.id,
            host_id=cmd.host_id,
            action=cmd.action,
            payload=cmd.payload,
            created_at=cmd.created_at,
            timeout_seconds=payload.timeout_seconds,
        ),
    )


@router.get("/commands", response_model=AgentResponseEnvelope[List[AgentCommandEnvelope]], dependencies=[Depends(verify_agent_auth)])
async def poll_agent_commands(
    host_id: str = Query(..., description="Unique ID of host agent querying for commands"),
    db: AsyncSession = Depends(get_db),
):
    """Poll for pending commands dispatched to a remote host agent daemon."""
    dispatcher = AgentCommandDispatcher(db)
    cmds = await dispatcher.get_pending_commands(host_id)
    envelopes = [
        AgentCommandEnvelope(
            command_id=c.id,
            host_id=c.host_id,
            action=c.action,
            payload=c.payload,
            created_at=c.created_at,
        )
        for c in cmds
    ]
    return AgentResponseEnvelope(
        status="success",
        message=f"Retrieved {len(envelopes)} command(s) for host '{host_id}'",
        data=envelopes,
    )


@router.post("/commands/{command_id}/result", response_model=AgentResponseEnvelope[Dict[str, Any]], dependencies=[Depends(verify_agent_auth)])
async def submit_command_result(
    command_id: str,
    payload: AgentCommandResult,
    db: AsyncSession = Depends(get_db),
):
    """Record execution result reported back by host agent daemon."""
    dispatcher = AgentCommandDispatcher(db)
    try:
        cmd = await dispatcher.record_command_result(command_id, payload)
        return AgentResponseEnvelope(
            status="success",
            message=f"Command '{command_id}' result recorded with status '{cmd.status}'",
            data={"command_id": cmd.id, "status": cmd.status, "success": payload.success},
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
