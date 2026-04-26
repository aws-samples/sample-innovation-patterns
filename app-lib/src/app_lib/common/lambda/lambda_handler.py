# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Handler-based Lambda entry point.

A simple Lambda handler that receives an event dict and returns a response dict.
Customize this for your use case: event processing, scheduled tasks, S3 triggers, etc.

This handler is deployed using the same ECR image as the REST Lambda.
The Lambda Web Adapter proxies the Lambda event as an HTTP POST to port 8080.
This module includes a minimal HTTP server that receives the POST, calls
handler(), and returns the result.

Deploy with:
    deploy_handler_lambda(
        stack_name="my-handler",
        function_name="my-handler-fn",
        image_uri=image_uri,
        region="us-east-1",
    )
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from loguru import logger


def handler(event, context=None):
    """Lambda entry point.

    Demo handler that supports two actions:
    - echo: returns the event data back
    - info: returns function metadata from the Lambda context

    Args:
        event: Lambda event dict. Expected shape: {"action": "echo"|"info", "data": ...}
        context: Unused (Lambda Web Adapter does not pass context)

    Returns:
        Response dict with statusCode and body
    """
    logger.info(f"Handler invoked with event: {json.dumps(event, default=str)}")

    action = event.get("action", "echo")

    if action == "echo":
        return {
            "statusCode": 200,
            "body": json.dumps({"action": "echo", "data": event.get("data")}),
        }

    if action == "info":
        import os

        info = {
            "action": "info",
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME"),
            "memory_limit_mb": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"),
        }
        return {"statusCode": 200, "body": json.dumps(info)}

    return {
        "statusCode": 400,
        "body": json.dumps({"error": f"Unknown action: {action}"}),
    }


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that bridges Lambda Web Adapter to handler()."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        event = json.loads(body)
        result = handler(event)
        response_body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self):
        """Health check for Lambda Web Adapter readiness."""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default stderr logging — loguru handles it."""
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), _Handler)  # nosec B104 — Lambda Web Adapter requires 0.0.0.0
    logger.info("Handler Lambda server listening on port 8080")
    server.serve_forever()
