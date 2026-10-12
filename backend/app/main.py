"""Network Control Plane — Main FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.api.router import api_router
import app.models.host  # noqa: F401
import app.models.network  # noqa: F401
import app.models.container  # noqa: F401
import app.models.job  # noqa: F401
import app.models.audit  # noqa: F401
import app.models.policy  # noqa: F401
import app.models.drift  # noqa: F401
import app.models.ai  # noqa: F401
import app.models.settings  # noqa: F401
import app.models.user  # noqa: F401
import app.models.agent_command  # noqa: F401





@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager to auto-create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Network Control Plane API",
    description="Provider-neutral control plane for application & workload networking.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 endpoints
app.include_router(api_router)

# Instrument Prometheus Metrics on /metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["System"])


@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "product": "Network Control Plane",
        "version": "1.0.0",
    }


from pathlib import Path
from fastapi.responses import Response

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"


@app.get("/install.sh", tags=["Agent Bootstrap"])
async def serve_install_sh():
    """Serve automated Linux host agent installer script."""
    sh_path = SCRIPTS_DIR / "install.sh"
    if sh_path.exists():
        content = sh_path.read_text(encoding="utf-8")
    else:
        content = "#!/usr/bin/env bash\necho 'Installer script not found'\n"
    return Response(content=content, media_type="text/x-shellscript")


@app.get("/install.ps1", tags=["Agent Bootstrap"])
async def serve_install_ps1():
    """Serve automated Windows PowerShell host agent installer script."""
    ps_path = SCRIPTS_DIR / "install.ps1"
    if ps_path.exists():
        content = ps_path.read_text(encoding="utf-8")
    else:
        content = "Write-Host 'Installer script not found'"
    return Response(content=content, media_type="text/plain")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
