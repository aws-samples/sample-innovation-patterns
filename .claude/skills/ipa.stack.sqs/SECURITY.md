# Security Advisory: ipa.stack.sqs

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage this stack.

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| `sqs:CreateQueue` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Create the queue and optional DLQ |
| `sqs:DeleteQueue` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Stack teardown |
| `sqs:GetQueueAttributes` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | CloudFormation status checks |
| `sqs:SetQueueAttributes` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Update queue configuration |
| `sqs:TagQueue` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Apply tags |
| `sqs:UntagQueue` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Remove tags |
| `sqs:GetQueueUrl` | `arn:aws:sqs:{region}:{account}:{ns}-{env}-*` | Resolve queue URL from name |

## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks (e.g., Lambda) to interact with the queue at runtime. These are NOT required for deployment — they belong in the consuming stack's execution role.

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| `sqs:SendMessage` | `{QueueArn}` | Producer Lambda sends messages to queue |
| `sqs:GetQueueAttributes` | `{QueueArn}` | Producer/consumer checks queue state |
| `sqs:ReceiveMessage` | `{QueueArn}` | Worker Lambda polls for messages (via ESM) |
| `sqs:DeleteMessage` | `{QueueArn}` | Worker Lambda acknowledges processed messages |
| `sqs:ChangeMessageVisibility` | `{QueueArn}` | Worker Lambda extends processing time |

## Security Controls (Hardcoded)

| Control | Setting | Notes |
|---------|---------|-------|
| Encryption at rest | SQS-managed SSE by default | Optional KMS CMK via KmsKeyArn parameter |
| Encryption in transit | Queue policy denies non-SSL requests | `aws:SecureTransport: false` -> Deny |
| Public access | None | IAM-only access, no public queue URLs |
| Dead-letter queue | Enabled by default (CreateDLQ=true) | Messages moved to DLQ after MaxReceiveCount failures |
| DLQ retention | 14 days | Maximum retention to allow investigation of failed messages |

## Known Deferrals

| Deferral | Rationale |
|----------|-----------|
| No DLQ CloudWatch alarm | POC scope — add `ApproximateNumberOfMessagesVisible > 0` alarm before production |
| No FIFO queue support | POC scope — standard queue sufficient for initial use cases |
| No content-based deduplication | Standard queue — FIFO-only feature |
| No message filtering | POC scope — all messages processed by single consumer |
