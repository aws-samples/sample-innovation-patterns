---
title: Overview
sidebar_position: 1
---

# Backend

The backend stack is a consolidated tier that deploys a fully serverless API. It provisions a Lambda function packaged as a container image (pulled from ECR), fronted by an API Gateway v2 HTTP API with JWT authorization via Amazon Cognito. DynamoDB tables are created on demand through feature flags, enabling patterns to opt in to persistence without template changes. CloudWatch dashboards and alarms provide built-in observability covering Lambda health, API Gateway metrics, Bedrock usage, and application-level error rates. The stack supports both buffered and streaming (SSE) invocation modes through separate API Gateway integrations.

**Template:** `infra/cfn/backend/backend.yml`
**Lifecycle:** deploy (tier)
**Capabilities:** `CAPABILITY_NAMED_IAM`

## Features

- Container-packaged Lambda with ECR image support and optional CMD override
- HTTP API (API Gateway v2) with a JWT authorizer backed by Cognito
- Buffered and streaming (SSE) route integrations on the same API
- Feature-flagged DynamoDB tables via `EnablePassengersTable` (PAY_PER_REQUEST billing, SSE enabled)
- Optional SQS integration via `EnableSqsIntegration` for queue-based patterns
- Per-function IAM execution role with least-privilege policies (no wildcard DynamoDB ARNs)
- CloudWatch dashboard with Lambda invocation/duration/error widgets, API Gateway request/latency/error widgets, and Bedrock token/latency/throttle widgets
- Metric-filter-driven alarms for application error rate and unhandled exception rate
- 30-day log retention on both Lambda and API Gateway log groups
- CORS configuration on the HTTP API (configurable origins, methods, and headers)

## When to Use

This stack is the compute and API layer in every IPA pattern that serves a REST API. It is included automatically by the `react-rest-lambda` pattern during composition. When composed alongside `sqs-lambda`, the backend gains SQS send permissions and the `SQS_QUEUE_URL` environment variable through the `EnableSqsIntegration` feature flag, which the compose skill enables automatically. Any pattern that requires a Lambda-backed HTTP endpoint should include this stack.
