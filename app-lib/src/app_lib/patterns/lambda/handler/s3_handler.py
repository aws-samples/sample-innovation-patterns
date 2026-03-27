"""S3 file processor handler.

Receives S3 event notifications via SQS. Downloads file, processes content,
writes results. Deploy with: deploy-handler-lambda handler_module="s3_handler"

Demo implementation processes CSV files and analyzes rows with Bedrock.
Customize process_file() for your use case.
"""

import csv
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3
from loguru import logger

from app_lib.service.data.titanic_passenger.titanic_passenger_data_service import (
    TitanicPassengerDataService,
)
from app_lib.service.inference.passenger_analysis_service import (
    PassengerAnalysisService,
)

s3 = boto3.client("s3")
passenger_service = TitanicPassengerDataService()
analysis_service = PassengerAnalysisService()


def process_file(bucket: str, key: str) -> int:
    """Process an uploaded file.

    Demo: Parse CSV rows and analyze each with Bedrock.
    Customize this function for your use case.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Number of records processed
    """
    logger.info(f"Processing s3://{bucket}/{key}")

    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")

    if not key.endswith(".csv"):
        logger.warning(f"Skipping non-CSV file: {key}")
        return 0

    reader = csv.DictReader(io.StringIO(content))
    processed = 0

    for row in reader:
        ticket = row.get("ticket")
        if not ticket:
            continue

        # Analyze with Bedrock
        result = analysis_service.analyze(row)

        # Update passenger record with analysis
        passenger = passenger_service.get(ticket)
        if passenger:
            passenger.analysis = json.dumps(result)
            passenger_service.save(passenger)
            processed += 1

    logger.info(f"Processed {processed} rows from {key}")
    return processed


def handle_s3_event(record: dict) -> int:
    """Extract bucket/key from S3 event record and process."""
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    return process_file(bucket, key)


class _Handler(BaseHTTPRequestHandler):
    """HTTP handler bridging Lambda Web Adapter to S3 processing."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        total = 0
        # SQS records contain S3 event as JSON string in body
        for sqs_record in body.get("Records", []):
            s3_event = json.loads(sqs_record["body"])
            for s3_record in s3_event.get("Records", []):
                total += handle_s3_event(s3_record)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"processed": total}).encode())

    def do_GET(self):
        """Health check for Lambda Web Adapter readiness."""
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    logger.info("S3 handler listening on port 8080")
    HTTPServer(("0.0.0.0", 8080), _Handler).serve_forever()  # nosec B104 — Lambda Web Adapter requires 0.0.0.0
