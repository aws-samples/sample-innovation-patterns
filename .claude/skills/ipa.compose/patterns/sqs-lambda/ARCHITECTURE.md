# Architecture: sqs-lambda Pattern

Event-driven background processing add-on to `react-rest-lambda`. Deploys SQS-based job processing infrastructure as composable CloudFormation stacks.

## System Architecture

```text
Layer 2:  [ESM]  ──▶ SQS (source), Lambda fn-worker (target)
Layer 1:  [Lambda fn-worker] ──▶ ECR (image), DynamoDB ddb-jobs (data), Cognito (JWT), SQS (receive)
          [Lambda fn]         ──▶ ... existing + SQS (send, queue URL)
Layer 0:  [SQS]  [DynamoDB ddb-jobs]  [ECR (shared)]  [Cognito (shared)]
```

## Event-Driven Processing Flow

```text
User -> API Gateway -> REST Lambda (fn)
                         |
                         +-- POST /api/v1/jobs -> DynamoDB (jobs, PENDING) + SQS
                         +-- GET  /api/v1/jobs/{id} -> DynamoDB (jobs)
                         +-- GET  /api/v1/jobs -> DynamoDB (jobs)

SQS Queue -> Event Source Mapping -> Worker Lambda (fn-worker)
                                       +-- DynamoDB (jobs) — status updates
                                       +-- Bedrock — AI inference
  +-- DLQ (after 3 failures)
```

## Stack Inventory

| Stack | Layer | Suffix | Purpose | Status |
|-------|-------|--------|---------|--------|
| ipa.stack.sqs | 0 | sqs | SQS queue with DLQ | New |
| ipa.stack.dynamodb | 0 | ddb-jobs | Job tracking table | New (reuses template) |
| ipa.stack.lambda | 1 | fn-worker | SQS consumer with Bedrock | New (reuses template) |
| ipa.stack.sqs-esm | 2 | esm | SQS-to-Lambda event source mapping | New |
| ipa.stack.ecr | 0 | ecr | Container image repository | Shared (from react-rest-lambda) |
| ipa.stack.cognito | 0 | cognito | Authentication | Shared (from react-rest-lambda) |
| ipa.stack.lambda | 1 | fn | REST handler (updated with SQS wiring) | Shared (from react-rest-lambda) |

## Deployment Order

Stacks deploy bottom-up (Layer 0 -> 2). Within a layer, stacks have no mutual dependencies. Teardown is reverse order (Layer 2 -> 0), with ESM torn down first to prevent orphaned triggers.

## Security Model

- **No wildcard IAM ARNs** — SQS send/receive permissions scoped to specific queue ARNs
- **Conditional IAM policies** — SQS permissions only created when corresponding ARN parameters are non-empty
- **SQS-managed encryption** — SSE enabled by default, optional KMS CMK
- **Queue policy** — denies non-SSL requests
- **No public queue access** — IAM-only authentication
- **DLQ** — poison messages captured after MaxReceiveCount failures

## Deployment Assumptions

- `react-rest-lambda` pattern is already composed and deployed (cognito, ecr, fn stacks exist)
- AWS credentials configured with Builder Execution Role permissions
- `.env` file with `APP_NAMESPACE` and `APP_ENV` set
- Container image includes `sqs_handler` module (part of app-lib)
- Worker Lambda resolves jobs table name by convention via `PynamodbUtil.env_table_name('jobs')`
