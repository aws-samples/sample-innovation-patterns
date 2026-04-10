# Queue Tier Template — Agent Context

Consolidated queue tier: SQS + DLQ + worker Lambda + ESM + DynamoDB (feature-flagged) + CloudWatch.

Template: `infra/cfn/queue/queue.yml`

## DynamoDB Customization — 4-Touchpoint Workflow

Same pattern as the backend tier. Adding, renaming, or removing a DynamoDB table requires coordinated changes across 4 files.

### The 4 Touchpoints

1. **This template** (`queue.yml`) — Parameter + Condition + Resource + IAM + Output
2. **PynamoDB model** (`app-lib/src/app_lib/features/{name}/models/`) — `PynamodbUtil.env_table_name("{suffix}")` must match the CFN table suffix
3. **Makefile** (`scripts/deploy.mk`) — `Enable{Name}Table=true` in `--parameter-overrides`
4. **App registration** — SQS handler imports the model

### Naming Contract

```
CFN TableName:  {Namespace}_{Environment}_{suffix}
PynamoDB:       PynamodbUtil.env_table_name("{suffix}")
```

### Common Operations

#### Add a new table (e.g., `results`)

1. **queue.yml Section 1**: Add `EnableResultsTable` parameter (default `'false'`)
2. **queue.yml Section 2**: Add `HasResultsTable: !Equals [!Ref EnableResultsTable, 'true']`
3. **queue.yml Section 3**: Copy `JobsTable`, rename to `ResultsTable`, change suffix to `_results`
4. **queue.yml Section 5**: Add conditional DynamoDB IAM policy with `!GetAtt ResultsTable.Arn`
5. **queue.yml Outputs**: Add `ResultsTableArn` with `Condition: HasResultsTable`
6. **PynamoDB model**: Create model with `PynamodbUtil.env_table_name("results")`
7. **Makefile**: Add `EnableResultsTable=true` to `deploy-queue` parameter overrides
8. **SQS handler**: Import and use the results model

## SQS Customization

| Parameter | Default | What It Controls |
|-----------|---------|-----------------|
| QueueName | `jobs` | Logical queue name (physical: `{Namespace}-{Environment}-{QueueName}`) |
| VisibilityTimeout | `300` | Must exceed worker Lambda timeout |
| MessageRetentionPeriod | `345600` | 4 days — max 14 days |
| MaxReceiveCount | `3` | Failed attempts before DLQ |
| CreateDLQ | `true` | Set `false` to skip DLQ creation |

### Section Navigation

| Section | Contents |
|---------|----------|
| 1: Parameters | Core, wirable, SQS config, worker Lambda config, DDB feature flags, CloudWatch |
| 2: Conditions | Feature flag conditions (HasDLQ, HasJobsTable, HasImageCommand, HasAlarmTopic) |
| 3: DynamoDB Tables | Conditional table resources |
| 4: SQS Queue | Queue + DLQ + deny non-SSL policy |
| 5: Lambda Worker | Execution role + IAM policies + function + log group |
| 6: Event Source Mapping | SQS → Worker Lambda trigger |
| 7: CloudWatch | Queue depth alarm + DLQ alarm + worker metric filters + dashboard |
| 8: Outputs | Stack outputs |

## Internal Wiring

All connections handled internally via `!Ref`/`!GetAtt`:

- `EventSourceArn: !GetAtt Queue.Arn` — ESM → SQS
- `FunctionName: !GetAtt WorkerLambdaFunction.Arn` — ESM → Worker Lambda
- `Resource: !GetAtt Queue.Arn` — Worker IAM → SQS (receive)
- `Resource: !GetAtt JobsTable.Arn` — Worker IAM → DynamoDB
- `deadLetterTargetArn: !GetAtt DeadLetterQueue.Arn` — Queue → DLQ
- `LogGroupName: !Ref WorkerLogGroup` — Metric filters → Worker logs

## Deploy Ordering

Queue deploys **before** backend (S2:B). Backend receives queue outputs (QueueUrl, QueueArn) via wirable parameters for SQS send permissions.

## Security Properties

- SQS: Deny non-SSL policy, SQS-managed SSE
- Lambda: Per-function execution role, SQS receive policy always present
- IAM: Conditional DynamoDB policies scoped to `!GetAtt Table.Arn` — no wildcards
- IAM: No `CrossTierTableArns` parameter (K2:B — convention-based ARN only)
- CloudWatch: 30-day log retention
