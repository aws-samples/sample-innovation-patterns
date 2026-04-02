"""Unit tests for app_lib.util.observability module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app_lib.util.observability import (
    log_bedrock_usage,
    log_exception,
    parse_bedrock_token_usage,
    publish_metric,
)


class TestLogException:
    """Tests for log_exception()."""

    def test_log_exception_emits_json(self, capsys):
        """Verify log_exception produces valid JSON with required fields."""
        with patch("app_lib.util.observability.logger") as mock_logger:
            exc = ValueError("test error")
            log_exception(exc, path="/api/v1/test", method="GET")

            mock_logger.error.assert_called_once()
            logged = json.loads(mock_logger.error.call_args[0][0])
            assert logged["level"] == "ERROR"
            assert logged["exception"] == "ValueError"
            assert logged["message"] == "test error"
            assert logged["path"] == "/api/v1/test"
            assert logged["method"] == "GET"
            assert logged["status_code"] == 500

    def test_log_exception_includes_context(self):
        """Verify optional context dict appears in output."""
        with patch("app_lib.util.observability.logger") as mock_logger:
            exc = RuntimeError("boom")
            log_exception(
                exc,
                path="/api/v1/items",
                method="POST",
                status_code=503,
                context={"traceback": "line 42"},
            )

            logged = json.loads(mock_logger.error.call_args[0][0])
            assert logged["status_code"] == 503
            assert logged["context"] == {"traceback": "line 42"}


class TestPublishMetric:
    """Tests for publish_metric()."""

    def test_publish_metric_calls_boto3(self):
        """Mock _get_cw_client and verify put_metric_data called correctly."""
        mock_client = MagicMock()
        with patch(
            "app_lib.util.observability._get_cw_client",
            return_value=mock_client,
        ):
            publish_metric(
                "TestMetric",
                42.0,
                unit="Count",
                dimensions={"Env": "dev"},
            )

            mock_client.put_metric_data.assert_called_once()
            call_kwargs = mock_client.put_metric_data.call_args[1]
            metric_data = call_kwargs["MetricData"][0]
            assert metric_data["MetricName"] == "TestMetric"
            assert metric_data["Value"] == 42.0
            assert metric_data["Unit"] == "Count"
            assert {"Name": "Env", "Value": "dev"} in metric_data[
                "Dimensions"
            ]

    def test_publish_metric_swallows_errors(self):
        """Verify boto3 errors don't propagate."""
        mock_client = MagicMock()
        mock_client.put_metric_data.side_effect = Exception("AWS error")
        with patch(
            "app_lib.util.observability._get_cw_client",
            return_value=mock_client,
        ):
            # Should not raise
            publish_metric("FailMetric", 1.0)


class TestParsBedrockTokenUsage:
    """Tests for parse_bedrock_token_usage()."""

    def test_parse_bedrock_converse_format(self):
        """Verify token extraction from Converse API response."""
        response = {
            "usage": {"inputTokens": 150, "outputTokens": 300},
            "output": {"message": {"content": []}},
        }
        tokens = parse_bedrock_token_usage(response)
        assert tokens["input_tokens"] == 150
        assert tokens["output_tokens"] == 300

    def test_parse_bedrock_legacy_format(self):
        """Verify token extraction from legacy response headers."""
        response = {
            "ResponseMetadata": {
                "HTTPHeaders": {
                    "x-amzn-bedrock-input-token-count": "100",
                    "x-amzn-bedrock-output-token-count": "200",
                }
            }
        }
        tokens = parse_bedrock_token_usage(response)
        assert tokens["input_tokens"] == 100
        assert tokens["output_tokens"] == 200

    def test_parse_bedrock_missing_tokens(self):
        """Verify zero defaults when fields missing."""
        tokens = parse_bedrock_token_usage({})
        assert tokens["input_tokens"] == 0
        assert tokens["output_tokens"] == 0


class TestLogBedrockUsage:
    """Tests for log_bedrock_usage()."""

    def test_log_bedrock_usage_publishes_metrics(self):
        """Mock publish_metric, verify both input/output metrics emitted."""
        with (
            patch(
                "app_lib.util.observability.publish_metric"
            ) as mock_publish,
            patch("app_lib.util.observability.logger"),
        ):
            response = {
                "usage": {"inputTokens": 50, "outputTokens": 100},
            }
            log_bedrock_usage("anthropic.claude-3-sonnet", response)

            assert mock_publish.call_count == 2
            calls = mock_publish.call_args_list
            assert calls[0][0] == ("BedrockInputTokens", 50)
            assert calls[0][1]["dimensions"] == {
                "ModelId": "anthropic.claude-3-sonnet"
            }
            assert calls[1][0] == ("BedrockOutputTokens", 100)


class TestMetricNamespace:
    """Tests for metric namespace construction."""

    def test_metric_namespace_from_env(self):
        """Verify namespace constructed from APP_NAMESPACE + APP_ENV."""
        with patch.dict(
            "os.environ",
            {"APP_NAMESPACE": "myapp", "APP_ENV": "staging"},
        ):
            # Re-import to pick up new env vars
            import importlib

            import app_lib.util.observability as obs

            importlib.reload(obs)
            assert obs._METRIC_NAMESPACE == "myapp/staging"
