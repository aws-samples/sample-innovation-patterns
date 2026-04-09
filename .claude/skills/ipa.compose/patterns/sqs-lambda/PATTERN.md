# Pattern: sqs-lambda

Event-driven background processing add-on to `react-rest-lambda`. Deploys an SQS queue with DLQ, a jobs DynamoDB table, a worker Lambda (SQS consumer with Bedrock access), and an event source mapping connecting SQS to the worker. Also wires the existing REST Lambda (fn) with SQS send permissions and queue URL for job submission.

**Compose-only pattern** — requires `react-rest-lambda` to be deployed first. Shares cognito, ecr, and fn stacks from the base pattern.

## Stack Sequence

1. ipa.stack.sqs — SQS queue + DLQ
   - Depends on: none
   - Suffix: sqs

2. ipa.stack.dynamodb — Jobs tracking table
   - Depends on: none
   - Suffix: ddb-jobs

3. ipa.stack.lambda — Worker Lambda (SQS consumer + Bedrock)
   - Depends on: ipa.stack.ecr (shared), ipa.stack.cognito (shared), ipa.stack.sqs, ipa.stack.dynamodb (ddb-jobs)
   - Suffix: fn-worker
   - Config: FunctionName=fn-worker InvokeMode=BUFFERED Timeout=300 ImageCommand=python,-m,sqs_handler

4. ipa.stack.sqs-esm — Event source mapping (SQS -> fn-worker)
   - Depends on: ipa.stack.lambda (fn-worker), ipa.stack.sqs
   - Suffix: esm

**Shared stacks** (from react-rest-lambda — not deployed by this pattern):
- ipa.stack.cognito (suffix: cognito) — AuthIssuer, AuthAudience for fn-worker
- ipa.stack.ecr (suffix: ecr) — ImageUri for fn-worker
- ipa.stack.lambda (suffix: fn) — updated with SqsQueueUrl, SqsSendQueueArns from sqs

## Teardown Sequence

1. ipa.stack.sqs-esm (suffix: esm)
2. ipa.stack.lambda (suffix: fn-worker)
3. ipa.stack.dynamodb (suffix: ddb-jobs)
4. ipa.stack.sqs (suffix: sqs)

## Wiring

```yaml
wiring:
  # --- Internal wiring (within sqs-lambda pattern) ---

  # SQS -> Worker Lambda — queue ARN for receive IAM policy
  - source:
      stack: sqs
      output: QueueArn
    target:
      stack: fn-worker
      parameter: SqsReceiveQueueArns
    notes: "SQS queue ARN for worker Lambda receive permissions"

  # DynamoDB (jobs) -> Worker Lambda — table ARN for IAM policy
  - source:
      stack: ddb-jobs
      output: TableArn
    target:
      stack: fn-worker
      parameter: DynamoDbTableArns
    notes: "Jobs table ARN for worker Lambda CRUD permissions"

  # Worker Lambda -> ESM — function ARN for event source
  - source:
      stack: fn-worker
      output: FunctionArn
    target:
      stack: esm
      parameter: FunctionArn
    notes: "Worker Lambda ARN for SQS event source mapping"

  # SQS -> ESM — queue ARN for event source
  - source:
      stack: sqs
      output: QueueArn
    target:
      stack: esm
      parameter: QueueArn
    notes: "SQS queue ARN for event source mapping"

  # --- Cross-pattern wiring (to existing react-rest-lambda stacks) ---

  # ECR -> Worker Lambda — container image
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: fn-worker
      parameter: ImageUri
    notes: "Container image URI — compose appends :$(IMAGE_TAG)"

  # Cognito -> Worker Lambda — OIDC issuer
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: fn-worker
      parameter: AuthIssuer
    notes: "Cognito OIDC issuer URL for JWT validation"

  # Cognito -> Worker Lambda — client ID
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: fn-worker
      parameter: AuthAudience
    notes: "Cognito app client ID for JWT audience validation"

  # SQS -> REST Lambda (fn) — queue URL as env var
  - source:
      stack: sqs
      output: QueueUrl
    target:
      stack: fn
      parameter: SqsQueueUrl
    notes: "SQS queue URL -> SQS_QUEUE_URL env var for job submission"

  # SQS -> REST Lambda (fn) — queue ARN for send permissions
  - source:
      stack: sqs
      output: QueueArn
    target:
      stack: fn
      parameter: SqsSendQueueArns
    notes: "SQS queue ARN for REST Lambda send permissions"

  # Convention-based connections (not wired):
  # - Worker Lambda -> Jobs DDB: table name resolved at runtime via PynamodbUtil.env_table_name('jobs')
```

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| SQS-1 | No DLQ CloudWatch alarm | POC scope — add before production |
| SQS-2 | No FIFO queue support | POC scope — standard queue sufficient |
| SQS-3 | No SSE streaming for job status | Deferred to react-rest-lambda composition (feature flag TBD) |

## Post-Deploy

None — infrastructure-only pattern. No data loading, no frontend configuration, no post-deploy wiring steps.
