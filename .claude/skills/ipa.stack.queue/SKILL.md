# ipa.stack.queue

Deploy a queue tier stack: SQS + DLQ + worker Lambda + ESM + DynamoDB (feature-flagged) + CloudWatch.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-queue` |
| Template | `infra/cfn/queue/queue.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | deploy (solution stack) |
| Tier | queue |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Namespace | Yes | — | Project namespace prefix |
| Environment | Yes | — | Deployment environment (dev/staging/prod) |
| ImageUri | Yes | — | ECR image URI with tag |
| AuthIssuer | Yes | — | Cognito OIDC issuer URL |
| AuthAudience | Yes | — | Cognito app client ID |
| QueueName | No | `jobs` | Logical queue name |
| VisibilityTimeout | No | `300` | Message visibility timeout (seconds) |
| MessageRetentionPeriod | No | `345600` | Message retention (seconds, default 4 days) |
| MaxReceiveCount | No | `3` | Attempts before DLQ |
| CreateDLQ | No | `true` | Create dead-letter queue |
| FunctionName | No | `fn-worker` | Worker Lambda name |
| MemorySize | No | `512` | Worker Lambda memory (MB) |
| Timeout | No | `300` | Worker Lambda timeout (seconds) |
| ImageCommand | No | `python,-m,sqs_handler` | Worker container CMD |
| EnableJobsTable | No | `false` | Feature flag: create jobs DynamoDB table |
| AlarmSnsTopicArn | No | *(empty)* | SNS topic for alarm actions |

## Feature Flags

| Flag | Default | Condition | Controls |
|------|---------|-----------|----------|
| EnableJobsTable | `false` | HasJobsTable | JobsTable resource, DynamoDB IAM policy, JobsTableArn output |
| CreateDLQ | `true` | HasDLQ | DeadLetterQueue resource, DlqUrl/DlqArn outputs, DLQ depth alarm |

## Wirable Parameters

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| ImageUri | ecr | RepositoryUri | Append `:$(IMAGE_TAG)` |
| AuthIssuer | cognito | IssuerUrl | OIDC issuer URL |
| AuthAudience | cognito | UserPoolClientId | App client ID |

## Outputs

| Output | Export Name | Description |
|--------|------------|-------------|
| QueueUrl | `{StackName}-QueueUrl` | Consumed by backend → SqsQueueUrl |
| QueueArn | `{StackName}-QueueArn` | Consumed by backend → SqsSendQueueArns |
| QueueName | `{StackName}-QueueName` | Physical queue name |
| WorkerFunctionArn | `{StackName}-WorkerFunctionArn` | Worker Lambda ARN |
| WorkerFunctionName | `{StackName}-WorkerFunctionName` | Worker Lambda name |
| DlqUrl | `{StackName}-DlqUrl` | Conditional (HasDLQ) |
| DlqArn | `{StackName}-DlqArn` | Conditional (HasDLQ) |
| JobsTableArn | `{StackName}-JobsTableArn` | Conditional (HasJobsTable) |
| DashboardUrl | `{StackName}-DashboardUrl` | Queue CloudWatch dashboard URL |

## Security

- SQS: Deny non-SSL policy, SQS-managed SSE
- Lambda: Per-function execution role, SQS receive policy always present
- IAM: Conditional DynamoDB policies scoped to `!GetAtt Table.Arn`
- CloudWatch: Log groups with 30-day retention
- No CrossTierTableArns parameter (K2:B — convention-based ARN only)

## Deploy Order

Queue deploys **before** backend (S2:B). Backend receives queue outputs via wirable parameters.

## Local Dev Environment

After deployment, the `update-env-sqs` target in `scripts/env.mk` writes `SQS_QUEUE_URL` to `.env`:

| Variable | Source Output | Description |
|----------|--------------|-------------|
| SQS_QUEUE_URL | QueueUrl | SQS queue URL for job submission |

This enables the local FastAPI backend (`load_dotenv()`) to submit jobs to the deployed queue without manual `.env` configuration. The target runs as part of `post-deploy.mk`'s `update-env` step, gated by `.env` existence (skipped in CI/CD).

## Deploy Command

```bash
aws cloudformation deploy \
  --template-file infra/cfn/queue/queue.yml \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-queue \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Namespace=$(APP_NAMESPACE) \
    Environment=$(APP_ENV) \
    ImageUri=$(REPO_URI):$(IMAGE_TAG) \
    AuthIssuer=$(AUTH_ISSUER) \
    AuthAudience=$(AUTH_AUDIENCE) \
    EnableJobsTable=true
```
