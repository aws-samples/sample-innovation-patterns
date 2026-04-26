# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Bedrock-powered passenger analysis using Converse API with structured output."""

import json
import os

import boto3
from loguru import logger

TOOL_SPEC = {
    "toolSpec": {
        "name": "passenger_analysis",
        "description": "Structured analysis of a Titanic passenger",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "survival_assessment": {
                        "type": "string",
                        "description": "Brief assessment of survival factors",
                    },
                    "risk_factors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key risk factors identified",
                    },
                    "historical_context": {
                        "type": "string",
                        "description": "Relevant historical context",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["HIGH", "MEDIUM", "LOW"],
                    },
                },
                "required": [
                    "survival_assessment",
                    "risk_factors",
                    "historical_context",
                    "confidence",
                ],
            }
        },
    }
}


class PassengerAnalysisService:
    """Analyze a Titanic passenger record via Bedrock Converse API."""

    def __init__(self):
        """Initialize the Bedrock runtime client."""
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=os.environ.get("APP_REGION", "us-east-1"),
        )
        self.model_id = os.environ.get(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
        )

    def analyze(self, passenger: dict) -> dict:
        """Call Bedrock with passenger data, return structured analysis dict."""
        logger.info(f"Analyzing passenger: {passenger.get('ticket', 'unknown')}")

        response = self.client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": (
                                "Analyze this Titanic passenger and assess their survival factors. "
                                f"Passenger data: {json.dumps(passenger)}"
                            )
                        }
                    ],
                }
            ],
            toolConfig={
                "tools": [TOOL_SPEC],
                "toolChoice": {"tool": {"name": "passenger_analysis"}},
            },
        )

        tool_use = next(
            block["toolUse"]
            for block in response["output"]["message"]["content"]
            if "toolUse" in block
        )
        return tool_use["input"]
