"""Application observability utilities.

Provides structured error logging, custom CloudWatch metric emission,
and Bedrock response token parsing for application-level observability.
Used by the exception middleware in rest/app.py.

CloudWatch metric filters in ipa.stack.app-cloudwatch parse the JSON
fields emitted by these functions. Changing field names here requires
updating the corresponding FilterPattern in the CloudFormation template.
"""

import json
import os
from typing import Any

import boto3
from loguru import logger

# Custom metric namespace — matches the CloudFormation template convention
_METRIC_NAMESPACE = os.environ.get(
    "APP_METRIC_NAMESPACE",
    f"{os.environ.get('APP_NAMESPACE', 'app')}/{os.environ.get('APP_ENV', 'dev')}",
)

# Lazy-init CloudWatch client (avoid import-time boto3 calls)
_cw_client = None


def _get_cw_client():
    """Return a lazily-initialized CloudWatch client.

    Returns:
        boto3 CloudWatch client instance.
    """
    global _cw_client
    if _cw_client is None:
        _cw_client = boto3.client(
            "cloudwatch",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
    return _cw_client


def log_exception(
    exc: Exception,
    *,
    path: str = "",
    method: str = "",
    status_code: int = 500,
    context: dict[str, Any] | None = None,
) -> None:
    """Emit a structured JSON log line for an unhandled exception.

    The JSON format is parsed by the UnhandledExceptions metric filter
    in the app-cloudwatch CloudFormation template.

    Args:
        exc: The exception instance.
        path: Request path (e.g., /api/v1/passengers).
        method: HTTP method (e.g., GET).
        status_code: HTTP status code returned.
        context: Additional key-value pairs to include in the log.
    """
    entry = {
        "level": "ERROR",
        "exception": type(exc).__name__,
        "message": str(exc),
        "path": path,
        "method": method,
        "status_code": status_code,
    }
    if context:
        entry["context"] = context
    logger.error(json.dumps(entry))


def publish_metric(
    metric_name: str,
    value: float,
    unit: str = "Count",
    dimensions: dict[str, str] | None = None,
) -> None:
    """Publish a custom metric to CloudWatch.

    Args:
        metric_name: Metric name (e.g., BedrockInputTokens).
        value: Metric value.
        unit: CloudWatch unit (Count, Milliseconds, etc.).
        dimensions: Optional dimension key-value pairs.
    """
    dim_list = [
        {"Name": k, "Value": v} for k, v in (dimensions or {}).items()
    ]
    try:
        _get_cw_client().put_metric_data(
            Namespace=_METRIC_NAMESPACE,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": dim_list,
                }
            ],
        )
    except Exception as e:
        # Never let metric emission break the request
        logger.warning(f"Failed to publish metric {metric_name}: {e}")


def parse_bedrock_token_usage(response: dict) -> dict[str, int]:
    """Extract token counts from a Bedrock InvokeModel response.

    Supports both Converse API and legacy InvokeModel response formats.

    Args:
        response: The full Bedrock API response dict.

    Returns:
        Dict with 'input_tokens' and 'output_tokens' keys (0 if not found).
    """
    # Converse API format
    usage = response.get("usage", {})
    if usage:
        return {
            "input_tokens": usage.get("inputTokens", 0),
            "output_tokens": usage.get("outputTokens", 0),
        }
    # Legacy InvokeModel — check response metadata
    metadata = response.get("ResponseMetadata", {})
    headers = metadata.get("HTTPHeaders", {})
    return {
        "input_tokens": int(
            headers.get("x-amzn-bedrock-input-token-count", 0)
        ),
        "output_tokens": int(
            headers.get("x-amzn-bedrock-output-token-count", 0)
        ),
    }


def log_bedrock_usage(
    model_id: str,
    response: dict,
) -> None:
    """Log Bedrock token usage and publish custom metrics.

    Call after every Bedrock InvokeModel/Converse call.

    Args:
        model_id: The Bedrock model ID used.
        response: The full Bedrock API response.
    """
    tokens = parse_bedrock_token_usage(response)
    dims = {"ModelId": model_id}
    if tokens["input_tokens"]:
        publish_metric(
            "BedrockInputTokens", tokens["input_tokens"], dimensions=dims
        )
    if tokens["output_tokens"]:
        publish_metric(
            "BedrockOutputTokens", tokens["output_tokens"], dimensions=dims
        )
    entry = {
        "level": "INFO",
        "bedrock_usage": True,
        "model_id": model_id,
        "input_tokens": tokens["input_tokens"],
        "output_tokens": tokens["output_tokens"],
    }
    logger.info(json.dumps(entry))
