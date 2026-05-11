---
title: Overview
sidebar_position: 1
---

# Queue

The queue stack is a consolidated deploy tier for event-driven background processing. It provisions an SQS standard queue with an optional dead-letter queue, a container-packaged worker Lambda triggered through an EventSourceMapping, a feature-flagged DynamoDB table for job tracking, and a full CloudWatch observability layer. The stack is included via `/ipa-compose` when the application needs asynchronous processing, and deploys before the backend tier so that queue outputs can be wired into backend parameters.

**Template:** `infra/cfn/queue/queue.yml`
**Lifecycle:** Deploy (tier)
**Capabilities:** `CAPABILITY_NAMED_IAM`

## Features

- SQS standard queue with configurable visibility timeout (default 300 s) and message retention (default 4 days).
- Dead-letter queue with configurable max receive count, created by default (`CreateDLQ=true`). Failed messages are retained for 14 days.
- Container-packaged worker Lambda triggered by EventSourceMapping with a batch size of 1. Reserved concurrency is set to 10.
- Feature-flagged DynamoDB jobs table (`EnableJobsTable`), provisioned on demand with pay-per-request billing and server-side encryption.
- Per-function IAM execution role with least-privilege policies scoped to the queue ARN and, conditionally, the jobs table ARN.
- Built-in Bedrock `InvokeModel` and `InvokeModelWithResponseStream` permissions for AI workloads.
- CloudWatch dashboard with queue depth, oldest message age, worker invocations, duration percentiles, errors, throttles, and custom metric filters.
- Queue depth alarm (threshold: 100 messages for 5 minutes) and DLQ depth alarm (threshold: 1 message), both wirable to an SNS topic.
- Deny non-SSL queue policy enforced via `aws:SecureTransport` condition, with SQS-managed server-side encryption enabled on all queues.
- 30-day CloudWatch log retention on the worker log group.

## When to Use

Include the queue stack when the application requires asynchronous job processing, long-running inference calls, or any work that should execute outside the synchronous API request path. When the queue and backend stacks are both selected during composition, the backend tier automatically receives SQS send permissions through wired `QueueUrl` and `QueueArn` parameters. No manual cross-stack configuration is required.
