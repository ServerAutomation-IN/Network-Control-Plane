"""Main API Router Aggregator — Network Control Plane"""

from fastapi import APIRouter
from app.api.v1.hosts import router as hosts_router
from app.api.v1.networks import router as networks_router
from app.api.v1.containers import router as containers_router
from app.api.v1.audit import router as audit_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.topology import router as topology_router
from app.api.v1.ipam import router as ipam_router
from app.api.v1.agent import router as agent_router
from app.api.v1.policies import router as policies_router
from app.api.v1.drift import router as drift_router
from app.api.v1.ai import router as ai_router
from app.api.v1.settings import router as settings_router

from app.api.v1.auth import router as auth_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.cloud_webhooks import router as cloud_webhooks_router
from app.api.v1.gitops import router as gitops_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.secrets import router as secrets_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(hosts_router)
api_router.include_router(networks_router)
api_router.include_router(containers_router)
api_router.include_router(audit_router)
api_router.include_router(jobs_router)
api_router.include_router(topology_router)
api_router.include_router(ipam_router)
api_router.include_router(agent_router)
api_router.include_router(policies_router)
api_router.include_router(drift_router)
api_router.include_router(ai_router)
api_router.include_router(settings_router)
api_router.include_router(auth_router)
api_router.include_router(webhooks_router)
api_router.include_router(cloud_webhooks_router)
api_router.include_router(gitops_router)
api_router.include_router(tasks_router)
api_router.include_router(secrets_router)




