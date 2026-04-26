# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Pydantic DTOs for the streaming inference endpoint."""

from pydantic import BaseModel, Field


class ConverseTurn(BaseModel):
    """A single message in the conversation."""

    role: str = "user"
    text: str = Field(..., min_length=1)


class ConverseRequest(BaseModel):
    """Request body for POST /api/v1/sse/inference/converse."""

    model_id: str = Field(..., min_length=1)
    messages: list[ConverseTurn] = Field(..., min_length=1, max_length=1)
    system_prompt: str = ""
    temperature: float | None = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
