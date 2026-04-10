# Pattern: sqs-lambda

Event-driven background processing add-on to `react-rest-lambda`. Deploys a queue tier (SQS + DLQ + worker Lambda + ESM + DynamoDB feature-flagged + CloudWatch) and wires the existing backend Lambda with SQS send permissions for job submission.

**Compose-only pattern** — requires `react-rest-lambda` to be deployed first. Shares cognito and ecr prepare stacks from the base pattern.

## Stack Sequence

1. ipa.stack.queue (deploy) — Queue tier: SQS + DLQ + worker Lambda + ESM + DynamoDB (feature-flagged) + CloudWatch
   - Depends on: ipa.stack.ecr (shared), ipa.stack.cognito (shared)
   - Suffix: queue
   - Config: FunctionName=fn-worker InvokeMode=BUFFERED Timeout=300 ImageCommand=python,-m,sqs_handler EnableJobsTable=true

**Deploy ordering**: Queue deploys **before** backend (S2:B). Backend receives queue outputs via wirable parameters.

**Shared stacks** (from react-rest-lambda — not deployed by this pattern):
- ipa.stack.cognito (suffix: cognito) — AuthIssuer, AuthAudience for fn-worker
- ipa.stack.ecr (suffix: ecr) — ImageUri for fn-worker
- ipa.stack.backend (suffix: backend) — updated with EnableSqsIntegration=true, SqsQueueUrl, SqsSendQueueArns from queue

## Teardown Sequence

1. ipa.stack.queue (suffix: queue)

Note: Backend is NOT torn down by this pattern — it belongs to react-rest-lambda.

## Wiring

```yaml
wiring:
  # --- Internal wiring (within queue template) ---
  # All SQS→worker, DDB→worker, and ESM connections are handled internally
  # via !GetAtt and !Ref within infra/cfn/queue/queue.yml.

  # --- Cross-stack wiring (prepare → queue) ---

  # ECR → Queue — container image for worker Lambda
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: queue
      parameter: ImageUri
    notes: "Container image URI — compose appends :$(IMAGE_TAG) (resolved from scripts/util/version.py at build/deploy time)"

  # Cognito → Queue — OIDC issuer for worker Lambda
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: queue
      parameter: AuthIssuer
    notes: "Cognito OIDC issuer URL for JWT validation"

  # Cognito → Queue — client ID for worker Lambda
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: queue
      parameter: AuthAudience
    notes: "Cognito app client ID for JWT audience validation"

  # --- Cross-pattern wiring (queue → backend) ---

  # Queue → Backend — queue URL as env var
  - source:
      stack: queue
      output: QueueUrl
    target:
      stack: backend
      parameter: SqsQueueUrl
    notes: "SQS queue URL → SQS_QUEUE_URL env var for job submission"

  # Queue → Backend — queue ARN for send permissions
  - source:
      stack: queue
      output: QueueArn
    target:
      stack: backend
      parameter: SqsSendQueueArns
    notes: "SQS queue ARN for REST Lambda send permissions"

  # Convention-based connections (not wired):
  # - Worker Lambda → Jobs DDB: table name resolved at runtime via PynamodbUtil.env_table_name('jobs')
```

## Backend Updates

When this pattern is composed with `react-rest-lambda`, the backend stack receives additional parameters:

| Parameter | Value | Source |
|-----------|-------|--------|
| EnableSqsIntegration | `true` | Enables SQS send IAM policy + SQS_QUEUE_URL env var |
| SqsQueueUrl | `$(eval ...)` | From queue stack QueueUrl output |
| SqsSendQueueArns | `$(eval ...)` | From queue stack QueueArn output |

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| SQS-1 | No FIFO queue support | POC scope — standard queue sufficient |
| SQS-2 | No SSE streaming for job status | Deferred to react-rest-lambda composition (feature flag TBD) |

## Shared Post-Deploy

When this pattern is composed with `react-rest-lambda`, the following post-deploy steps are modified:

### configure-frontend

Additional CLI arguments:
- `--enable-feature jobs` — Enable the jobs UI for SQS-based background processing

## Post-Deploy

None — infrastructure-only pattern. No data loading, no frontend configuration, no post-deploy wiring steps.
