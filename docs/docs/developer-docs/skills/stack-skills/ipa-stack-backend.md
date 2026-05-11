---
title: /ipa-stack-backend
sidebar_position: 2
---

# /ipa-stack-backend

Backend tier stack: Lambda function with API Gateway v2, optional DynamoDB tables, and a CloudWatch dashboard.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-backend` |
| Template | `infra/cfn/backend/backend.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | deploy |

## Parameters

### Wirable Parameters

These parameters are automatically wired from other stack outputs by `/ipa-compose`:

| Parameter | Source | Required |
|-----------|--------|----------|
| `ImageUri` | ecr.RepositoryUri | Yes |
| `AuthIssuer` | cognito.IssuerUrl | Yes |
| `AuthAudience` | cognito.UserPoolClientId | Yes |
| `SqsQueueUrl` | queue.QueueUrl | Conditional (when `EnableSqsIntegration` is true) |
| `SqsSendQueueArns` | queue.QueueArn | Conditional (when `EnableSqsIntegration` is true) |

### Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FunctionName` | `{namespace}-{env}-api` | Lambda function name |
| `MemorySize` | `512` | Lambda memory in MB |
| `Timeout` | `30` | Lambda timeout in seconds |
| `ImageCommand` | *(template default)* | Container image command override |

### Feature Flags

| Flag | Default | Effect |
|------|---------|--------|
| `EnablePassengersTable` | `false` | Creates a DynamoDB Passengers table |
| `EnableSqsIntegration` | `false` | Grants SQS send permissions and injects `SQS_QUEUE_URL` environment variable |

## Outputs

| Output | Description |
|--------|-------------|
| `ApiUrl` | HTTP API Gateway invoke URL |
| `FunctionArn` | Lambda function ARN |
| `FunctionName` | Lambda function name |
| `DashboardUrl` | CloudWatch dashboard URL |
| `PassengersTableArn` | DynamoDB table ARN (only when `EnablePassengersTable` is true) |

## Deploy Order

Backend deploys **after** Queue when both stacks are in the same pattern, because backend may need the Queue URL for SQS integration wiring.

## Related Skills

- [/ipa-stack-queue](./ipa-stack-queue.md) — Provides SQS wiring when `EnableSqsIntegration` is true
- [/ipa-stack-ecr](./ipa-stack-ecr.md) — Provides the container image URI
- [/ipa-stack-cognito](./ipa-stack-cognito.md) — Provides auth issuer and audience
- [/ipa-compose](../lifecycle-skills/ipa-compose.md) — Assembles this stack into deployment patterns
