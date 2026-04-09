---
name: ipa-stack-sqs
description: "Deploy an SQS queue with optional dead-letter queue for message processing."
---

# ipa.stack.sqs

Deploy an SQS queue with configurable visibility timeout, message retention, and optional dead-letter queue. Provides QueueUrl and QueueArn outputs for downstream Lambda stacks (send permissions, receive permissions, event source mapping). Supports optional KMS encryption for customer-managed keys.

## CloudFormation Contract

- **Template**: `infra/cfn/sqs/sqs.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-sqs` (single instance) or `{APP_NAMESPACE}-{APP_ENV}-sqs-{name}` (multi-instance)
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| QueueName | String | — | `/^[a-z][a-z0-9-]{0,29}$/` | "Must be 1-30 chars, lowercase letters/digits/hyphens, starts with letter" |
| VisibilityTimeout | Number | 900 | `0-43200` | "Must be between 0 and 43200 seconds" |
| MessageRetentionPeriod | Number | 345600 | `60-1209600` | "Must be between 60 and 1209600 seconds" |
| MaxReceiveCount | Number | 3 | `1-1000` | "Must be between 1 and 1000" |
| CreateDLQ | String | true | `true \| false` | "Must be true or false" |
| KmsKeyArn | String | (empty) | — | — |

### Parameter Classification

**Configuration** (6) — sourced from `.env` or defaults:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`
- VisibilityTimeout — default 900s (must exceed Lambda timeout)
- MessageRetentionPeriod — default 345600s (4 days)
- MaxReceiveCount — default 3 attempts before DLQ
- CreateDLQ — default true

**Pattern-provided** (1) — sourced from `.env` via convention:
- QueueName — logical queue name (e.g., `jobs`)

**Wirable — Optional** (1) — sourced from upstream stack outputs when composed:
- KmsKeyArn ← customer-managed KMS key (defaults to empty — uses SQS-managed SSE)

## Queue Naming Convention

Physical SQS queue names use hyphens (unlike DynamoDB which uses underscores): `{Namespace}-{Environment}-{QueueName}`.

Examples:
- Namespace=`app`, Environment=`dev`, QueueName=`jobs` -> `app-dev-jobs`
- DLQ: `app-dev-jobs-dlq`

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| QueueUrl | SQS queue URL for message operations | `{StackName}-QueueUrl` | ipa.stack.lambda (SqsQueueUrl parameter -> SQS_QUEUE_URL env var) |
| QueueArn | SQS queue ARN for IAM policies | `{StackName}-QueueArn` | ipa.stack.lambda (SqsSendQueueArns, SqsReceiveQueueArns), ipa.stack.sqs-esm (QueueArn) |
| QueueName | Physical queue name | `{StackName}-QueueName` | Monitoring, debugging |
| DlqUrl | DLQ URL (conditional — only when CreateDLQ=true) | `{StackName}-DlqUrl` | Monitoring |
| DlqArn | DLQ ARN (conditional — only when CreateDLQ=true) | `{StackName}-DlqArn` | Future CloudWatch alarm |

## Security Summary

**Required IAM actions**: sqs:CreateQueue, DeleteQueue, GetQueueAttributes, SetQueueAttributes, TagQueue, UntagQueue — scoped to `arn:aws:sqs:{region}:{account}:{ns}-{env}-*`
**Security controls**: SQS-managed SSE by default (optional KMS CMK), queue policy denying non-SSL, no public access, DLQ for poison messages
**Full advisory**: See [SECURITY.md](SECURITY.md)
