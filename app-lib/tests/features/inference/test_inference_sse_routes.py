# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for inference SSE streaming endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with auth disabled."""
    with patch.dict("os.environ", {"AUTH_ENABLED": "false"}):
        from app_lib.common.app import app

        return TestClient(app)


def _mock_stream_events():
    """Create a mock Bedrock converse_stream response with text chunks and metadata."""
    return [
        {"contentBlockDelta": {"delta": {"text": "Hello"}}},
        {"contentBlockDelta": {"delta": {"text": " world"}}},
        {
            "metadata": {
                "usage": {"inputTokens": 10, "outputTokens": 5},
            }
        },
    ]


def _parse_sse_events(response_text: str) -> list[str]:
    """Parse SSE data lines from response text."""
    events = []
    for line in response_text.split("\n"):
        if line.startswith("data: "):
            events.append(line[6:])
    return events


# ---------------------------------------------------------------------------
# US1: Streaming happy path
# ---------------------------------------------------------------------------


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_returns_text_chunks(mock_get_client, client):
    """Test POST /api/v1/sse/inference/converse streams text chunks."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": _mock_stream_events()}
    mock_get_client.return_value = mock_client

    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"

    events = _parse_sse_events(resp.text)
    text_events = [json.loads(e) for e in events if e.startswith("{") and "text" in e]
    assert len(text_events) == 2
    assert text_events[0]["text"] == "Hello"
    assert text_events[1]["text"] == " world"


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_returns_metadata(mock_get_client, client):
    """Test that metadata event with usage counts is emitted."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": _mock_stream_events()}
    mock_get_client.return_value = mock_client

    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    events = _parse_sse_events(resp.text)
    metadata_events = [
        json.loads(e) for e in events if e.startswith("{") and "metadata" in e
    ]
    assert len(metadata_events) == 1
    assert metadata_events[0]["metadata"]["usage"]["inputTokens"] == 10
    assert metadata_events[0]["metadata"]["usage"]["outputTokens"] == 5


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_ends_with_done(mock_get_client, client):
    """Test that stream always ends with [DONE] marker."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": _mock_stream_events()}
    mock_get_client.return_value = mock_client

    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    events = _parse_sse_events(resp.text)
    assert events[-1] == "[DONE]"


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_forwards_system_prompt(mock_get_client, client):
    """Test that system prompt is forwarded to Bedrock when provided."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "system_prompt": "You are a pirate.",
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    assert call_kwargs["system"] == [{"text": "You are a pirate."}]


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_omits_system_when_empty(mock_get_client, client):
    """Test that empty system prompt sends empty system list."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "system_prompt": "",
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    assert call_kwargs["system"] == []


# ---------------------------------------------------------------------------
# US2: Parameter configuration
# ---------------------------------------------------------------------------


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_custom_temperature(mock_get_client, client):
    """Test that custom temperature is passed to inference config."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "temperature": 0.2,
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    assert call_kwargs["inferenceConfig"]["temperature"] == 0.2


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_custom_max_tokens(mock_get_client, client):
    """Test that custom max_tokens is passed to inference config."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "max_tokens": 1024,
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    assert call_kwargs["inferenceConfig"]["maxTokens"] == 1024


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_defaults(mock_get_client, client):
    """Test that defaults are applied when parameters are omitted."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    config = call_kwargs["inferenceConfig"]
    assert config["maxTokens"] == 256
    assert config["temperature"] == 0.7
    assert "topP" not in config


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_temperature_precedence_over_top_p(mock_get_client, client):
    """Test that temperature takes precedence when both are provided."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "temperature": 0.5,
            "top_p": 0.9,
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    config = call_kwargs["inferenceConfig"]
    assert config["temperature"] == 0.5
    assert "topP" not in config


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_top_p_when_no_temperature(mock_get_client, client):
    """Test that top_p is used when temperature is null."""
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client

    client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
            "temperature": None,
            "top_p": 0.9,
        },
    )
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    config = call_kwargs["inferenceConfig"]
    assert config["topP"] == 0.9
    assert "temperature" not in config


# ---------------------------------------------------------------------------
# US3: Error handling
# ---------------------------------------------------------------------------


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_error_returns_error_event(mock_get_client, client):
    """Test that Bedrock errors are returned as SSE error events."""
    mock_client = MagicMock()
    mock_client.converse_stream.side_effect = Exception("Model not found: bad-model")
    mock_get_client.return_value = mock_client

    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "bad-model",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    error_events = [json.loads(e) for e in events if e.startswith("{") and "error" in e]
    assert len(error_events) == 1
    assert "Model not found" in error_events[0]["error"]


@patch("app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client")
def test_converse_stream_error_ends_with_done(mock_get_client, client):
    """Test that [DONE] is always the final event even after errors."""
    mock_client = MagicMock()
    mock_client.converse_stream.side_effect = Exception("Service unavailable")
    mock_get_client.return_value = mock_client

    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [{"role": "user", "text": "Hi"}],
        },
    )
    events = _parse_sse_events(resp.text)
    assert events[-1] == "[DONE]"


def test_converse_stream_validation_rejects_empty_messages(client):
    """Test that empty messages list returns 422."""
    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [],
        },
    )
    assert resp.status_code == 422


def test_converse_stream_validation_rejects_multiple_messages(client):
    """Test that multiple messages returns 422."""
    resp = client.post(
        "/api/v1/sse/inference/converse",
        json={
            "model_id": "us.anthropic.claude-sonnet-4-20250514",
            "messages": [
                {"role": "user", "text": "Hi"},
                {"role": "user", "text": "Hello"},
            ],
        },
    )
    assert resp.status_code == 422
