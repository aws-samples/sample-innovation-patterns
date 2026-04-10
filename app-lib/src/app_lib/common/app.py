"""FastAPI application entry point.

Mounts feature routers and defines infrastructure routes.

Run locally:
    cd common && make dev
"""

import os
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

load_dotenv()

from app_lib.common.auth import JWTAuthMiddleware
from app_lib.common.util.observability import log_exception

# Feature routers — delete import + include_router to disconnect a feature
from app_lib.features.passengers.routes.passenger_routes import (
    router as passengers_router,
)

# SQS pattern
from app_lib.features.jobs.routes.job_routes import job_router
from app_lib.features.jobs.routes.job_sse_routes import job_sse_router

# Inference streaming
from app_lib.features.inference.routes.inference_sse_routes import inference_sse_router

app = FastAPI(
    title="Titanic Passenger API",
    version="1.0.0",
    description="Example REST API. Customize for your own entity.",
    root_path=os.environ.get("API_STAGE_PREFIX", ""),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthMiddleware)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and emits structured error logs."""

    async def dispatch(self, request: Request, call_next):
        """Process request and catch unhandled exceptions."""
        try:
            return await call_next(request)
        except Exception as exc:
            log_exception(
                exc,
                path=request.url.path,
                method=request.method,
                context={"traceback": traceback.format_exc()},
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


app.add_middleware(ObservabilityMiddleware)

# Feature registration — 1 line per feature
app.include_router(passengers_router)

# SQS pattern
app.include_router(job_router)
app.include_router(job_sse_router)

# Inference streaming
app.include_router(inference_sse_router)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


def _get_version() -> str:
    """Get app version from env var or installed package metadata."""
    env_version = os.environ.get("APP_VERSION")
    if env_version and env_version != "unknown":
        return env_version
    try:
        from importlib.metadata import version

        return version("app-lib")
    except Exception:
        return "unknown"


@app.get("/version")
def version():
    """App version and build identifier."""
    return {
        "version": _get_version(),
        "build": os.environ.get("BUILD_VERSION", "dev"),
    }
