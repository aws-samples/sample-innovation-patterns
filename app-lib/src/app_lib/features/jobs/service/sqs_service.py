# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Thin wrapper around boto3 SQS send_message."""

import json
import os

import boto3


class SqsService:
    """Send messages to an SQS queue."""

    def __init__(self, queue_url: str = None):
        """Initialize the SQS client."""
        self.queue_url = queue_url or os.environ.get("SQS_QUEUE_URL")
        self.client = boto3.client(
            "sqs", region_name=os.environ.get("APP_REGION", "us-east-1")
        )

    def send_message(self, body: dict) -> str:
        """Send a JSON message to the queue. Returns MessageId."""
        resp = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(body),
        )
        return resp["MessageId"]
