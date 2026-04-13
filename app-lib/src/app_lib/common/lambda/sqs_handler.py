# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""SQS worker handler.

Receives SQS events via Lambda Web Adapter pass-through (POST /events).
Deploy with: deploy-handler-lambda handler_module="sqs_handler"
Requires env: AWS_LWA_PASS_THROUGH_PATH=/events

The handler reads each job from DynamoDB, calls Bedrock for analysis,
and writes the result back. Status transitions: PENDING -> PROCESSING -> COMPLETED|FAILED.
"""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from loguru import logger

from app_lib.common.service.inference.passenger_analysis_service import (
    PassengerAnalysisService,
)
from app_lib.features.jobs.service.job_data_service import JobDataService
from app_lib.features.passengers.service.passenger_data_service import (
    TitanicPassengerDataService,
)

job_service = JobDataService()
passenger_service = TitanicPassengerDataService()
analysis_service = PassengerAnalysisService()

PASSENGER_ATTRS = [
    "ticket",
    "name",
    "pclass",
    "survived",
    "sex",
    "age",
    "sibsp",
    "parch",
    "fare",
    "cabin",
    "embarked",
]


def process_job(job_id: str):
    """Load job from DDB, run inference, write result to passenger."""
    job = job_service.get(job_id)
    if not job:
        logger.error(f"Job not found: {job_id}")
        return

    now = datetime.now(timezone.utc).isoformat()
    job.status = "PROCESSING"
    job.updated_at = now
    job_service.save(job)

    try:
        input_data = json.loads(job.input_data)
        ticket = input_data["ticket"]
        passenger = passenger_service.get(ticket)
        if not passenger:
            raise ValueError(f"Passenger not found: {ticket}")

        passenger_dict = {
            attr: (
                int(v)
                if isinstance(v, (int, float))
                and attr in ("pclass", "survived", "sibsp", "parch")
                else float(v)
                if isinstance(v, (int, float))
                else v
            )
            for attr in PASSENGER_ATTRS
            if (v := getattr(passenger, attr, None)) is not None
        }

        result = analysis_service.analyze(passenger_dict)

        # Write analysis to passenger record
        passenger.analysis = json.dumps(result)
        passenger_service.save(passenger)

        # Job gets lightweight metadata, not the full result
        job.metadata = json.dumps({"ticket": ticket})
        job.status = "COMPLETED"
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = "FAILED"
        job.error = str(e)

    job.updated_at = datetime.now(timezone.utc).isoformat()
    job_service.save(job)


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that bridges Lambda Web Adapter to process_job()."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        for record in body.get("Records", []):
            msg = json.loads(record["body"])
            process_job(msg["job_id"])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'"success"')

    def do_GET(self):
        """Health check for Lambda Web Adapter readiness."""
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), _Handler)  # nosec B104 — Lambda Web Adapter requires 0.0.0.0
    logger.info("SQS handler listening on port 8080")
    server.serve_forever()
