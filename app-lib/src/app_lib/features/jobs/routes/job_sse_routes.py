"""SSE streaming route for job status updates.

Part of the SQS background processing pattern.
Mounted by app.py alongside job_routes.
"""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app_lib.features.jobs.routes.job_dto import JobResponse
from app_lib.features.jobs.service.job_data_service import JobDataService

job_sse_router = APIRouter(prefix="/api/v1/sse", tags=["sse"])

_job_service = JobDataService()


@job_sse_router.get("/jobs/{job_id}")
async def sse_job_status(job_id: str):
    """Stream job status updates via SSE. Closes on terminal status."""

    async def generate():
        last_status = None
        while True:
            job = _job_service.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                return
            if job.status != last_status:
                last_status = job.status
                payload = JobResponse.from_model(job).model_dump()
                yield f"data: {json.dumps(payload)}\n\n"
            if job.status in ("COMPLETED", "FAILED"):
                return
            await asyncio.sleep(1.5)

    return StreamingResponse(generate(), media_type="text/event-stream")
