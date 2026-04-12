---
title: Local Development
sidebar_position: 3
---

# Local Development

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide sets up a local development environment for iterating on backend and frontend code against deployed AWS infrastructure. By the end, the reader has the FastAPI backend running locally with hot-reload, the React frontend proxying API requests, and environment variables configured to use the deployed Cognito, DynamoDB, and API Gateway resources.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: after a successful /ipa.deploy when ready to start writing application code; switching between deployed environments; onboarding a new developer; troubleshooting backend or frontend code against live infrastructure.

## Before You Start

> **Guidance:** Prerequisites: /ipa.deploy completed, Python 3.12 installed, Node.js and npm installed, uv installed, .env configured with deployed stack outputs, AWS CLI configured.

## Before / Target State

> **Guidance:** Before: Deployed AWS infrastructure. No local servers running. Code changes require redeployment. After: FastAPI backend on localhost:8000 with hot-reload. React frontend on localhost:3000 with API proxy. Changes reflected immediately without redeployment.

## Steps

> **Guidance:** 4 steps. Source files: app-lib/ (Python backend, pyproject.toml, entrypoint), web-client/ (React frontend, package.json, proxy config), .env, scripts/env.mk.

### 1. Configure local environment variables

> **Guidance:** Explain which .env variables are needed for local dev and how to obtain them from deployed stack outputs.

### 2. Start the backend

> **Guidance:** Install Python dependencies with uv, run FastAPI with uvicorn in development mode.

### 3. Start the frontend

> **Guidance:** Install Node dependencies, configure the API proxy to point to the local backend, start the React dev server.

### 4. Verify local-to-cloud connectivity

> **Guidance:** Confirm the local backend reaches DynamoDB and the frontend authenticates through Cognito.

## Verification

> **Guidance:** curl localhost:8000/health to confirm backend. Open localhost:3000 to confirm frontend. Authenticate through Cognito and confirm a round-trip API call works end-to-end.

## Troubleshooting

> **Guidance:** Conditional section. Potential entries: CORS errors (proxy config fix), DynamoDB access denied (credentials or region), Cognito callback URL mismatch (must include localhost), port conflicts.

## Next Steps

> **Guidance:** Link to notebook-development guide, deploying changes guide, app-lib/ developer docs, web-client/ developer docs.
