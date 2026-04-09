---
name: ipa-stack-sqs-esm
description: "Deploy an SQS-to-Lambda event source mapping for automatic message processing."
---

# ipa.stack.sqs-esm

Deploy an SQS-to-Lambda event source mapping that connects an SQS queue to a Lambda function for automatic message processing. This is a terminal stack with no outputs — it exists solely to wire SQS to Lambda. Must be deployed after both SQS and Lambda stacks, and torn down before both.

## CloudFormation Contract

- **Template**: `infra/cfn/sqs-esm/sqs-esm.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-esm`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| FunctionArn | String | — | — | — |
| QueueArn | String | — | — | — |
| BatchSize | Number | 1 | `1-10000` | "Must be between 1 and 10000" |
| MaxBatchingWindowInSeconds | Number | 0 | `0-300` | "Must be between 0 and 300 seconds" |
| Enabled | String | true | `true \| false` | "Must be true or false" |

### Parameter Classification

**Configuration** (5) — sourced from `.env` or defaults:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`
- BatchSize — default 1 message per invocation
- MaxBatchingWindowInSeconds — default 0 (no batching window)
- Enabled — default true

**Wirable — Required** (2) — sourced from upstream stack outputs:
- FunctionArn <- ipa.stack.lambda `FunctionArn`
- QueueArn <- ipa.stack.sqs `QueueArn`

## Outputs

None — ESM is a terminal stack with no downstream consumers.

## Deployment Order Constraint

The event source mapping depends on both the SQS queue and the Lambda function existing. It must be:
- **Deployed last** — after both `ipa.stack.sqs` and `ipa.stack.lambda` (fn-worker)
- **Torn down first** — before either SQS or Lambda stacks (removing Lambda while ESM exists causes orphaned triggers)

## Security Summary

**Required IAM actions**: lambda:CreateEventSourceMapping, DeleteEventSourceMapping, GetEventSourceMapping, UpdateEventSourceMapping — scoped to `*` (AWS limitation — ESM ARNs are not predictable at deploy time)
**Security controls**: No additional IAM resources created — Lambda execution role must already have SQS receive permissions
**Full advisory**: See [SECURITY.md](SECURITY.md)
