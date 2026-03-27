"""SSE streaming routes.

Routes under /api/v1/sse/ are served via API Gateway STREAM integration.
Adding new SSE endpoints here requires no API Gateway changes —
the /api/v1/sse/{proxy+} catch-all covers them.
"""

import asyncio
import json
import os

import boto3
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app_lib.rest.v1.sse.playground_dto import ConverseRequest

sse_router = APIRouter(prefix="/api/v1/sse", tags=["sse"])


@sse_router.get("/echo")
async def sse_echo(message: str = "hello"):
    """Echo a message back as SSE events. For testing streaming integration."""

    async def generate():
        for i in range(5):
            yield f"data: {json.dumps({'seq': i, 'message': message})}\n\n"
            await asyncio.sleep(0.1)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

