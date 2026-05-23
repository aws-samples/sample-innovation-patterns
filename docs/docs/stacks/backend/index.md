---
title: Overview
sidebar_position: 1
---

# Backend

The backend stack is a consolidated tier that deploys a fully serverless API. It provisions a Lambda function packaged as a container image (pulled from ECR), fronted by an API Gateway v2 HTTP API with JWT authorization via Amazon Cognito. DynamoDB tables are created on demand through feature flags, enabling compositions to opt in to persistence without template changes. The stack supports both buffered and streaming (SSE) invocation modes through separate API Gateway integrations.

**Template:** `infra/cfn/backend/backend.yml`
**Lifecycle:** deploy (tier)
**Capabilities:** `CAPABILITY_NAMED_IAM`

## Features

- Container-packaged Lambda with ECR image support and optional CMD override
- HTTP API (API Gateway v2) with a JWT authorizer backed by Cognito
- Buffered and streaming (SSE) route integrations on the same API
- Feature-flagged DynamoDB tables via `EnablePassengersTable` (PAY_PER_REQUEST billing, SSE enabled)
- Optional SQS integration via `EnableSqsIntegration` for queue-based compositions
- Per-function IAM execution role with least-privilege policies (no wildcard DynamoDB ARNs)
- 30-day log retention on both Lambda and API Gateway log groups
- CORS configuration on the HTTP API (configurable origins, methods, and headers)

## When to Use

This stack is the compute and API layer. It is included via `/ipa-compose` when composing a serverless API. When the queue stack is also selected, the backend gains SQS send permissions through the `EnableSqsIntegration` feature flag, which the compose skill enables automatically. Any composition that requires a Lambda-backed HTTP endpoint should include this stack.
