---
title: /ipa-stack-queue
sidebar_position: 8
---

# /ipa-stack-queue

Queue tier stack: SQS queue with dead-letter queue, worker Lambda, Event Source Mapping, optional DynamoDB table, and CloudWatch dashboard.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-queue` |
| Template | `infra/cfn/queue/queue.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | deploy |

## Parameters

### Wirable Parameters

| Parameter | Source | Required |
|-----------|--------|----------|
| `ImageUri` | ecr.RepositoryUri | Yes |
| `AuthIssuer` | cognito.IssuerUrl | Yes |
| `AuthAudience` | cognito.UserPoolClientId | Yes |

### Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `QueueName` | `jobs` | SQS queue name suffix |
| `VisibilityTimeout` | `30` | Message visibility timeout in seconds |
| `MessageRetentionPeriod` | `345600` | Message retention in seconds (4 days) |
| `MaxReceiveCount` | `3` | Max receives before sending to DLQ |
| `CreateDLQ` | `true` | Whether to create a dead-letter queue |
| `FunctionName` | `{namespace}-{env}-worker` | Worker Lambda function name |
| `MemorySize` | `512` | Worker Lambda memory in MB |
| `Timeout` | `30` | Worker Lambda timeout in seconds |
| `ImageCommand` | *(template default)* | Container image command override |

### Feature Flags

| Flag | Default | Effect |
|------|---------|--------|
| `EnableJobsTable` | `false` | Creates a DynamoDB Jobs table for tracking queue processing |

## Outputs

| Output | Description |
|--------|-------------|
| `QueueUrl` | SQS queue URL |
| `QueueArn` | SQS queue ARN |
| `QueueName` | SQS queue name |
| `WorkerFunctionArn` | Worker Lambda function ARN |
| `WorkerFunctionName` | Worker Lambda function name |
| `DlqUrl` | Dead-letter queue URL (when `CreateDLQ` is true) |
| `DlqArn` | Dead-letter queue ARN (when `CreateDLQ` is true) |
| `JobsTableArn` | DynamoDB Jobs table ARN (when `EnableJobsTable` is true) |
| `DashboardUrl` | CloudWatch dashboard URL |

## Deploy Order

Queue deploys **before** Backend when both stacks are in the same pattern. This ensures the Queue URL and ARN are available for Backend's SQS integration wiring.

## Local Development

After deployment, the `update-env-sqs` Make target writes `SQS_QUEUE_URL` to `.env` for local development use.

## Wiring

The Queue stack provides outputs consumed by Backend:

| Consumer | Parameters Wired |
|----------|-----------------|
| Backend | `SqsQueueUrl` ← `QueueUrl`, `SqsSendQueueArns` ← `QueueArn` (when `EnableSqsIntegration` is true) |

## Related Skills

- [/ipa-stack-backend](./ipa-stack-backend.md) — Consumes queue URL and ARN for SQS integration
- [/ipa-stack-ecr](./ipa-stack-ecr.md) — Provides the container image URI
- [/ipa-stack-cognito](./ipa-stack-cognito.md) — Provides auth issuer and audience
- [/ipa-compose](../lifecycle-skills/ipa-compose.md) — Assembles this stack into deployment patterns
