"""v1 routes for the background jobs REST API.

Routes are defined on an APIRouter with prefix="/api/v1".
The router is mounted by the FastAPI app in app.py.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pynamodb.exceptions import ScanError

from app_lib.features.jobs.model.job_table import JobTable
from app_lib.features.jobs.routes.job_dto import JobCreate, JobResponse
from app_lib.features.jobs.service.job_data_service import JobDataService
from app_lib.features.jobs.service.sqs_service import SqsService

job_router = APIRouter(prefix="/api/v1", tags=["jobs"])

job_service = JobDataService()


def _get_sqs_service() -> SqsService:
    queue_url = os.environ.get("SQS_QUEUE_URL")
    if not queue_url:
        logger.warning(
            "SQS_QUEUE_URL not set — job submission disabled. "
            "Add SQS_QUEUE_URL to .env (see .env.example)."
        )
        raise HTTPException(
            status_code=503,
            detail="SQS_QUEUE_URL not configured. Deploy the SQS background processing pattern.",
        )
    return SqsService(queue_url)


_TABLE_UNAVAILABLE = (
    "Jobs table not available. Deploy the SQS background processing pattern."
)


@job_router.post("/jobs", response_model=JobResponse, status_code=202)
def submit_job(body: JobCreate):
    """Submit a new background job."""
    sqs = _get_sqs_service()

    now = datetime.now(timezone.utc).isoformat()
    job = JobTable(
        id=str(uuid.uuid4()),
        status="PENDING",
        job_type=body.job_type,
        input_data=json.dumps(body.input_data),
        created_at=now,
        updated_at=now,
    )
    try:
        job_service.save(job)
    except Exception as e:
        if "ResourceNotFoundException" in str(e):
            raise HTTPException(status_code=503, detail=_TABLE_UNAVAILABLE)
        raise
    sqs.send_message({"job_id": job.id})

    return JobResponse.from_model(job)


@job_router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    """Get a job by ID."""
    try:
        job = job_service.get(job_id)
    except Exception as e:
        if "ResourceNotFoundException" in str(e):
            raise HTTPException(status_code=503, detail=_TABLE_UNAVAILABLE)
        raise
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobResponse.from_model(job)


@job_router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
):
    """List jobs with optional filters."""
    filters = {
        k: v
        for k, v in {"status": status, "job_type": job_type}.items()
        if v is not None
    }
    try:
        results = job_service.query(limit=limit, **filters)
    except ScanError:
        raise HTTPException(status_code=503, detail=_TABLE_UNAVAILABLE)
    return [JobResponse.from_model(j) for j in results]
