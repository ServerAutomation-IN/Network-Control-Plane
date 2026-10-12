"""Inventory Synchronization Service — Network Control Plane

Orchestrates host discovery, data normalization, and atomic state persistence into PostgreSQL.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import secret_encryptor
from app.docker.adapter import DockerAdapter
from app.providers.factory import ProviderFactory
from app.models.host import InfrastructureHost
from app.models.network import Network, NetworkSubnet
from app.models.container import Container, ContainerNetwork
from app.schemas.host import HostCreate
from app.schemas.network import NetworkCreateRequest, ContainerAttachRequest
from app.services.audit import AuditService


class InventoryService:
    """Service handling infrastructure host inventory discovery and persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_host(self, payload: HostCreate) -> InfrastructureHost:
        """Register a new provider host, encrypting TLS certificates at rest."""
        host_id = f"host-{payload.name.lower().replace(' ', '-')}"

        stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
        existing_host = (await self.db.execute(stmt)).scalar_one_or_none()

        encrypted_tls = None
        raw_tls = payload.tls_cert or payload.encrypted_tls_cert
        if raw_tls:
            encrypted_tls = secret_encryptor.encrypt(raw_tls)

        if existing_host:
            existing_host.name = payload.name
            existing_host.endpoint = payload.endpoint
            existing_host.provider_type = payload.provider_type
            existing_host.environment = payload.environment
            if encrypted_tls:
                existing_host.encrypted_tls_cert = encrypted_tls
            host = existing_host
        else:
            now = datetime.now(timezone.utc)
            host = InfrastructureHost(
                id=host_id,
                name=payload.name,
                endpoint=payload.endpoint,
                provider_type=payload.provider_type,
                environment=payload.environment,
                status="REGISTERED",
                encrypted_tls_cert=encrypted_tls,
                last_seen=now,
                created_at=now,
            )
            self.db.add(host)

        await self.db.flush()

        await AuditService(self.db).log_event(
            action="REGISTER_HOST",
            resource_type="host",
            resource_id=host.id,
            risk_level="LOW",
            details={
                "name": payload.name,
                "endpoint": payload.endpoint,
                "environment": payload.environment,
                "provider_type": payload.provider_type,
                "has_tls_cert": bool(raw_tls),
            },
        )

        await self.db.commit()

        # Perform initial sync
        host = await self.sync_host(host_id=host.id, endpoint=host.endpoint)
        return host

    def get_decrypted_tls_cert(self, host: InfrastructureHost) -> str | None:
        """Decrypt host TLS certificate stored in encrypted_tls_cert."""
        if not host.encrypted_tls_cert:
            return None
        try:
            return secret_encryptor.decrypt(host.encrypted_tls_cert)
        except Exception:
            return None

    async def unregister_host(self, host_id: str) -> bool:
        """Unregister a provider host and delete associated inventory."""
        stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
        host = (await self.db.execute(stmt)).scalar_one_or_none()
        if not host:
            raise ValueError(f"Host '{host_id}' not found.")

        await AuditService(self.db).log_event(
            action="UNREGISTER_HOST",
            resource_type="host",
            resource_id=host.id,
            risk_level="HIGH",
            details={"name": host.name, "endpoint": host.endpoint},
        )

        await self.db.delete(host)
        await self.db.commit()
        return True

    async def sync_host(self, host_id: str, endpoint: str = "unix:///var/run/docker.sock") -> InfrastructureHost:
        """Discover and synchronize host networks and container endpoints into DB."""
        # 1. Fetch existing InfrastructureHost entity if present to resolve provider_type
        stmt = select(InfrastructureHost).where(InfrastructureHost.id == host_id)
        result = await self.db.execute(stmt)
        host = result.scalar_one_or_none()

        ptype = host.provider_type if host else "docker"
        adapter = ProviderFactory.get_adapter(provider_type=ptype, endpoint=endpoint)

        try:
            discovery_data = await adapter.discover()
            is_online = True
        except Exception:
            discovery_data = {}
            is_online = False

        if not host:
            now = datetime.now(timezone.utc)
            host = InfrastructureHost(
                id=host_id,
                name="Local Docker Host",
                endpoint=endpoint,
                provider_type="docker",
                environment="development",
                status="ONLINE" if is_online else "UNREACHABLE",
                docker_version=discovery_data.get("version"),
                os=discovery_data.get("os"),
                architecture=discovery_data.get("arch"),
                last_seen=now,
                created_at=now,
            )
            self.db.add(host)
        else:
            host.endpoint = endpoint
            host.status = "ONLINE" if is_online else "UNREACHABLE"
            if is_online:
                if discovery_data.get("version"):
                    host.docker_version = discovery_data.get("version")
                if discovery_data.get("os"):
                    host.os = discovery_data.get("os")
                if discovery_data.get("arch"):
                    host.architecture = discovery_data.get("arch")
            host.last_seen = datetime.now(timezone.utc)

        await self.db.flush()

        # 2. Sync Networks & Subnets
        raw_networks = discovery_data.get("networks", [])
        net_map: Dict[str, Network] = {}

        # Fetch existing networks for host
        existing_nets_stmt = select(Network).where(Network.host_id == host_id)
        existing_nets = (await self.db.execute(existing_nets_stmt)).scalars().all()
        existing_net_ref_map = {n.provider_ref_id: n for n in existing_nets}

        for net_data in raw_networks:
            pref_id = net_data["provider_ref_id"]
            if pref_id in existing_net_ref_map:
                net_entity = existing_net_ref_map[pref_id]
                net_entity.name = net_data["name"]
                net_entity.driver = net_data["driver"]
                net_entity.scope = net_data["scope"]
                net_entity.internal = net_data["internal"]
                net_entity.attachable = net_data["attachable"]
                net_entity.ingress = net_data["ingress"]
                net_entity.labels = net_data["labels"]
                net_entity.options = net_data["options"]
            else:
                net_entity = Network(
                    id=str(uuid.uuid4()),
                    host_id=host_id,
                    provider_ref_id=pref_id,
                    name=net_data["name"],
                    driver=net_data["driver"],
                    scope=net_data["scope"],
                    internal=net_data["internal"],
                    attachable=net_data["attachable"],
                    ingress=net_data["ingress"],
                    labels=net_data["labels"],
                    options=net_data["options"],
                )
                self.db.add(net_entity)

            await self.db.flush()
            net_map[net_data["name"]] = net_entity
            net_map[pref_id] = net_entity

            # Re-sync subnets
            await self.db.execute(delete(NetworkSubnet).where(NetworkSubnet.network_id == net_entity.id))
            for sub in net_data.get("subnets", []):
                subnet_entity = NetworkSubnet(
                    id=str(uuid.uuid4()),
                    network_id=net_entity.id,
                    subnet=sub.get("subnet"),
                    gateway=sub.get("gateway"),
                    ip_range=sub.get("ip_range"),
                )
                self.db.add(subnet_entity)

        # 3. Sync Containers & Attachments
        raw_containers = discovery_data.get("containers", [])
        existing_cnts_stmt = select(Container).where(Container.host_id == host_id)
        existing_cnts = (await self.db.execute(existing_cnts_stmt)).scalars().all()
        existing_cnt_ref_map = {c.provider_ref_id: c for c in existing_cnts}

        for cnt_data in raw_containers:
            pref_id = cnt_data["provider_ref_id"]
            if pref_id in existing_cnt_ref_map:
                cnt_entity = existing_cnt_ref_map[pref_id]
                cnt_entity.name = cnt_data["name"]
                cnt_entity.image = cnt_data["image"]
                cnt_entity.status = cnt_data["status"]
                cnt_entity.labels = cnt_data["labels"]
            else:
                cnt_entity = Container(
                    id=str(uuid.uuid4()),
                    host_id=host_id,
                    provider_ref_id=pref_id,
                    name=cnt_data["name"],
                    image=cnt_data["image"],
                    status=cnt_data["status"],
                    labels=cnt_data["labels"],
                )
                self.db.add(cnt_entity)

            await self.db.flush()

            # Re-sync container attachments
            await self.db.execute(delete(ContainerNetwork).where(ContainerNetwork.container_id == cnt_entity.id))
            for att in cnt_data.get("attachments", []):
                net_ref = att.get("network_ref_id") or att.get("network_name")
                target_net = net_map.get(net_ref) or net_map.get(att.get("network_name"))
                if target_net:
                    att_entity = ContainerNetwork(
                        id=str(uuid.uuid4()),
                        container_id=cnt_entity.id,
                        network_id=target_net.id,
                        ip_address=att.get("ip_address"),
                        ipv6_address=att.get("ipv6_address"),
                        mac_address=att.get("mac_address"),
                        aliases=att.get("aliases") or [],
                    )
                    self.db.add(att_entity)

        await self.db.commit()
        await self.db.refresh(host)
        return host

    async def create_network(self, payload: NetworkCreateRequest) -> Network:
        """Create a new network on provider host and persist entity."""
        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == payload.host_id)
        host = (await self.db.execute(host_stmt)).scalar_one_or_none()
        if not host:
            raise ValueError(f"Target host '{payload.host_id}' not found.")

        if host.endpoint.startswith("agent://"):
            from app.services.agent_dispatcher import AgentCommandDispatcher
            dispatcher = AgentCommandDispatcher(self.db)
            cmd = await dispatcher.enqueue_command(
                host_id=host.id,
                action="CREATE_NETWORK",
                payload={
                    "name": payload.name,
                    "driver": payload.driver,
                    "internal": payload.internal,
                    "attachable": payload.attachable,
                    "ingress": payload.ingress,
                    "labels": payload.labels,
                    "options": payload.options,
                    "subnets": [s.model_dump() for s in payload.subnets],
                },
            )
            raw_net = {"Id": f"agent-net-{cmd.id}", "Name": payload.name}
        else:
            adapter = DockerAdapter(base_url=host.endpoint)
            spec = {
                "name": payload.name,
                "driver": payload.driver,
                "internal": payload.internal,
                "attachable": payload.attachable,
                "labels": payload.labels,
            }
            raw_net = await adapter.create_network(spec)

        net_entity = Network(
            id=str(uuid.uuid4()),
            host_id=host.id,
            provider_ref_id=raw_net.get("Id") or str(uuid.uuid4()),
            name=payload.name,
            driver=payload.driver,
            scope=payload.scope,
            internal=payload.internal,
            attachable=payload.attachable,
            ingress=payload.ingress,
            labels=payload.labels,
            options=payload.options,
        )
        self.db.add(net_entity)
        await self.db.flush()

        for sub in payload.subnets:
            sub_entity = NetworkSubnet(
                id=str(uuid.uuid4()),
                network_id=net_entity.id,
                subnet=sub.subnet,
                gateway=sub.gateway,
                ip_range=sub.ip_range,
            )
            self.db.add(sub_entity)

        await AuditService(self.db).log_event(
            action="CREATE_NETWORK",
            resource_type="network",
            resource_id=net_entity.id,
            risk_level="LOW",
            details={"name": payload.name, "driver": payload.driver, "host_id": host.id},
        )

        await self.db.commit()
        await self.db.refresh(net_entity)
        return net_entity

    async def delete_network(self, network_id: str, force: bool = False) -> bool:
        """Evaluate pre-deletion safety and delete network entity."""
        from app.services.safety import PreDeletionSafetyEngine

        safety_engine = PreDeletionSafetyEngine(self.db)
        safety_assessment = await safety_engine.evaluate_network_deletion(network_id)

        if not safety_assessment.is_safe_to_delete and not force:
            raise ValueError(f"Network is unsafe to delete: {', '.join(safety_assessment.risk_factors)}")

        stmt = select(Network).where(Network.id == network_id)
        net = (await self.db.execute(stmt)).scalar_one_or_none()
        if not net:
            raise ValueError(f"Network '{network_id}' not found.")

        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == net.host_id)
        host = (await self.db.execute(host_stmt)).scalar_one_or_none()
        endpoint = host.endpoint if host else "unix:///var/run/docker.sock"

        if host and host.endpoint.startswith("agent://"):
            from app.services.agent_dispatcher import AgentCommandDispatcher
            dispatcher = AgentCommandDispatcher(self.db)
            await dispatcher.enqueue_command(
                host_id=host.id,
                action="DELETE_NETWORK",
                payload={"network_ref_id": net.provider_ref_id, "name": net.name},
            )
        else:
            adapter = DockerAdapter(base_url=endpoint)
            try:
                await adapter.delete_network(net.provider_ref_id)
            except Exception:
                # If provider removal fails, proceed to clean database record if forced
                if not force:
                    raise

        await AuditService(self.db).log_event(
            action="DELETE_NETWORK",
            resource_type="network",
            resource_id=net.id,
            risk_level=safety_assessment.risk_level,
            details={"name": net.name, "forced": force},
        )

        await self.db.delete(net)
        await self.db.commit()
        return True

    async def attach_container(self, network_id: str, payload: ContainerAttachRequest) -> ContainerNetwork:
        """Attach container workload endpoint to network."""
        net_stmt = select(Network).where(Network.id == network_id)
        net = (await self.db.execute(net_stmt)).scalar_one_or_none()
        if not net:
            raise ValueError(f"Network '{network_id}' not found.")

        cnt_stmt = select(Container).where((Container.id == payload.container_id) | (Container.provider_ref_id == payload.container_id))
        cnt = (await self.db.execute(cnt_stmt)).scalar_one_or_none()
        if not cnt:
            raise ValueError(f"Container '{payload.container_id}' not found.")

        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == net.host_id)
        host = (await self.db.execute(host_stmt)).scalar_one_or_none()
        endpoint = host.endpoint if host else "unix:///var/run/docker.sock"

        if host and host.endpoint.startswith("agent://"):
            from app.services.agent_dispatcher import AgentCommandDispatcher
            dispatcher = AgentCommandDispatcher(self.db)
            await dispatcher.enqueue_command(
                host_id=host.id,
                action="ATTACH_ENDPOINT",
                payload={
                    "network_ref_id": net.provider_ref_id,
                    "container_ref_id": cnt.provider_ref_id,
                    "ip_address": payload.ip_address,
                    "aliases": payload.aliases,
                },
            )
        else:
            adapter = DockerAdapter(base_url=endpoint)
            await adapter.connect_container(
                network_ref_id=net.provider_ref_id,
                container_ref_id=cnt.provider_ref_id,
                ipv4_address=payload.ip_address,
                aliases=payload.aliases,
            )

        att_entity = ContainerNetwork(
            id=str(uuid.uuid4()),
            container_id=cnt.id,
            network_id=net.id,
            ip_address=payload.ip_address,
            aliases=payload.aliases,
        )
        self.db.add(att_entity)

        await AuditService(self.db).log_event(
            action="ATTACH_CONTAINER",
            resource_type="network",
            resource_id=net.id,
            risk_level="LOW",
            details={"container_id": cnt.id, "container_name": cnt.name, "ip_address": payload.ip_address},
        )

        await self.db.commit()
        await self.db.refresh(att_entity)
        return att_entity

    async def detach_container(self, network_id: str, container_id: str) -> bool:
        """Detach container workload endpoint from network."""
        net_stmt = select(Network).where(Network.id == network_id)
        net = (await self.db.execute(net_stmt)).scalar_one_or_none()
        if not net:
            raise ValueError(f"Network '{network_id}' not found.")

        cnt_stmt = select(Container).where((Container.id == container_id) | (Container.provider_ref_id == container_id))
        cnt = (await self.db.execute(cnt_stmt)).scalar_one_or_none()
        if not cnt:
            raise ValueError(f"Container '{container_id}' not found.")

        host_stmt = select(InfrastructureHost).where(InfrastructureHost.id == net.host_id)
        host = (await self.db.execute(host_stmt)).scalar_one_or_none()
        endpoint = host.endpoint if host else "unix:///var/run/docker.sock"

        if host and host.endpoint.startswith("agent://"):
            from app.services.agent_dispatcher import AgentCommandDispatcher
            dispatcher = AgentCommandDispatcher(self.db)
            await dispatcher.enqueue_command(
                host_id=host.id,
                action="DETACH_ENDPOINT",
                payload={
                    "network_ref_id": net.provider_ref_id,
                    "container_ref_id": cnt.provider_ref_id,
                },
            )
        else:
            adapter = DockerAdapter(base_url=endpoint)
            await adapter.disconnect_container(network_ref_id=net.provider_ref_id, container_ref_id=cnt.provider_ref_id)

        await self.db.execute(
            delete(ContainerNetwork).where(
                ContainerNetwork.network_id == net.id,
                ContainerNetwork.container_id == cnt.id,
            )
        )

        await AuditService(self.db).log_event(
            action="DETACH_CONTAINER",
            resource_type="network",
            resource_id=net.id,
            risk_level="MEDIUM",
            details={"container_id": cnt.id, "container_name": cnt.name},
        )

        await self.db.commit()
        return True
