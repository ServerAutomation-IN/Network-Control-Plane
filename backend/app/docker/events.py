"""Docker Engine Events Listener — Network Control Plane

Streams runtime Docker events to Redis pub/sub for real-time inventory updates.
"""

import json
from typing import Any, Dict
import redis.asyncio as aioredis

from app.core.config import settings
from app.docker.client import DockerClientWrapper


class DockerEventListener:
    """Streams Docker runtime events to Redis Pub/Sub."""

    def __init__(self, base_url: str = "unix:///var/run/docker.sock"):
        self.client_wrapper = DockerClientWrapper(base_url=base_url)

    async def listen_and_publish(self):
        """Listen to Docker event stream and publish to Redis 'docker_events' channel."""
        if not self.client_wrapper.ping():
            return

        client = self.client_wrapper.get_client()
        redis_client = aioredis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

        try:
            # Stream Docker events filtered to networks and containers
            for event in client.events(decode=True, filters={"type": ["network", "container"]}):
                event_payload = {
                    "type": event.get("Type"),
                    "action": event.get("Action"),
                    "actor_id": event.get("Actor", {}).get("ID"),
                    "actor_attributes": event.get("Actor", {}).get("Attributes") or {},
                    "time": event.get("time"),
                }
                await redis_client.publish("docker_events", json.dumps(event_payload))
        except Exception:
            pass
        finally:
            await redis_client.aclose()
