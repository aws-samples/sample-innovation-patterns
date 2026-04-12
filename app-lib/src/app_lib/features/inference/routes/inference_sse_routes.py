# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""SSE streaming route for inference via Bedrock Converse API.

Mounted by app.py. Provides POST /api/v1/sse/inference/converse.
"""

import json
import os

import boto3
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app_lib.features.inference.routes.inference_dto import ConverseRequest

inference_sse_router = APIRouter(prefix="/api/v1/sse", tags=["inference"])


def _get_bedrock_client():
    """Create Bedrock runtime client."""
    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ.get("APP_REGION", "us-east-1"),
    )


@inference_sse_router.post("/inference/converse")
async def inference_converse_stream(body: ConverseRequest):
    """Stream Bedrock Converse API response as SSE events."""
    client = _get_bedrock_client()

    inference_config: dict = {"maxTokens": body.max_tokens}
    if body.temperature is not None:
        inference_config["temperature"] = body.temperature
    elif body.top_p is not None:
        inference_config["topP"] = body.top_p

    async def generate():
        try:
            response = client.converse_stream(
                modelId=body.model_id,
                messages=[
                    {"role": m.role, "content": [{"text": m.text}]}
                    for m in body.messages
                ],
                system=[{"text": body.system_prompt}] if body.system_prompt else [],
                inferenceConfig=inference_config,
            )
            stream = response.get("stream")
            if not stream:
                yield f'data: {json.dumps({"error": "No stream in response"})}\n\n'
                yield "data: [DONE]\n\n"
                return
            for event in stream:
                if "contentBlockDelta" in event:
                    text = event["contentBlockDelta"]["delta"]["text"]
                    yield f"data: {json.dumps({'text': text})}\n\n"
                if "metadata" in event:
                    usage = event["metadata"].get("usage", {})
                    yield f"data: {json.dumps({'metadata': {'usage': usage}})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
