"""FastAPI application entry point.

Mounts versioned API routers and defines infrastructure routes.

Run locally:
    make run
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Load .env file if present (e.g., APP_REGION, APP_ENV for local dev)

# SQS pattern — remove these 2 imports and 2 include_router calls to disconnect
# Bedrock KB pattern — remove these 2 lines to disconnect
# Agent Core Chat pattern — remove these 2 imports and 2 include_router calls to disconnect
from app_lib.patterns.bedrock.agent_core.chat.routes.chat_routes import chat_router
from app_lib.patterns.bedrock.agent_core.chat.routes.chat_sse_routes import (
    chat_sse_router,
)
from app_lib.patterns.bedrock.kb.routes.kb_sse_routes import kb_sse_router
from app_lib.patterns.sqs.routes.job_routes import job_router
from app_lib.patterns.sqs.routes.job_sse_routes import job_sse_router
from app_lib.rest.v1.passengers.routes import router as v1_router
from app_lib.rest.v1.sse.routes import sse_router

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

from app_lib.rest.auth import JWTAuthMiddleware

app.add_middleware(JWTAuthMiddleware)

# --- Observability middleware ---
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app_lib.util.observability import log_exception


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and emits structured error logs."""

    async def dispatch(self, request: Request, call_next):
        """Process request and catch unhandled exceptions.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The response from the next handler, or a 500 JSON response.
        """
        try:
            response = await call_next(request)
            return response
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

app.include_router(v1_router)
app.include_router(sse_router)
app.include_router(job_router)  # SQS pattern
app.include_router(job_sse_router)  # SQS pattern
app.include_router(kb_sse_router)  # Bedrock KB pattern
app.include_router(chat_router)  # Agent Core Chat pattern
app.include_router(chat_sse_router)  # Agent Core Chat pattern


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
