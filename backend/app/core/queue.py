"""ARQ Async Worker Queue & Task Runner — Network Control Plane

Manages background job dispatching, retries, and execution workers using ARQ and Redis.
"""

from typing import Any, Dict
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings


def get_redis_settings() -> RedisSettings:
    """Get ARQ Redis settings."""
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
    )


async def create_arq_pool() -> ArqRedis:
    """Create ARQ Redis connection pool for dispatching jobs."""
    return await create_pool(get_redis_settings())


async def sample_background_job(ctx: Dict[str, Any], job_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sample background worker task execution handler."""
    return {
        "job_id": job_id,
        "action": action,
        "status": "COMPLETED",
        "result": payload,
    }


class WorkerSettings:
    """ARQ Worker process settings."""
    functions = [sample_background_job]
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 300
