# ipa.stack.backend

Deploy a backend tier stack: Lambda + API Gateway v2 + DynamoDB (feature-flagged) + CloudWatch.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-backend` |
| Template | `infra/cfn/backend/backend.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | deploy (solution stack) |
| Tier | backend |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Namespace | Yes | — | Project namespace prefix |
| Environment | Yes | — | Deployment environment (dev/staging/prod) |
| ImageUri | Yes | — | ECR image URI with tag |
| AuthIssuer | Yes | — | Cognito OIDC issuer URL |
| AuthAudience | Yes | — | Cognito app client ID |
| FunctionName | No | `fn` | Lambda function name |
| InvokeMode | No | `RESPONSE_STREAM` | Lambda invocation mode |
| MemorySize | No | `512` | Lambda memory in MB |
| Timeout | No | `300` | Lambda timeout in seconds |
| ImageCommand | No | *(empty)* | Override container CMD |
| AllowedOrigin | No | `https://none.invalid` | Allowed CORS origin (CloudFront domain from post-deploy). Blocks cross-origin requests until set. |
| EnablePassengersTable | No | `false` | Feature flag: create passengers DynamoDB table |
| EnableSqsIntegration | No | `false` | Feature flag: enable SQS send permissions |
| SqsQueueUrl | No | *(empty)* | SQS queue URL for env var injection |
| SqsSendQueueArns | No | *(empty)* | SQS queue ARNs for send IAM policy |
| AlarmSnsTopicArn | No | *(empty)* | SNS topic for alarm actions |

## Feature Flags

| Flag | Default | Condition | Controls |
|------|---------|-----------|----------|
| EnablePassengersTable | `false` | HasPassengersTable | PassengersTable resource, DynamoDB IAM policy, PassengersTableArn output |
| EnableSqsIntegration | `false` | HasSqsIntegration | SQS_QUEUE_URL env var, SQS send IAM policy |

## Wirable Parameters

Parameters that receive values from other stacks during composition:

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| ImageUri | ecr | RepositoryUri | Append `:$(IMAGE_TAG)` |
| AuthIssuer | cognito | IssuerUrl | OIDC issuer URL |
| AuthAudience | cognito | UserPoolClientId | App client ID |
| SqsQueueUrl | queue | QueueUrl | Only when EnableSqsIntegration=true |
| SqsSendQueueArns | queue | QueueArn | Only when EnableSqsIntegration=true |
| AllowedOrigin | frontend | AppUrl | Set during post-deploy (update-backend-cors target) |

## Outputs

| Output | Export Name | Description |
|--------|------------|-------------|
| ApiUrl | `{StackName}-ApiUrl` | HTTP API invoke URL |
| FunctionArn | `{StackName}-FunctionArn` | Lambda function ARN |
| FunctionName | `{StackName}-FunctionName` | Lambda function name |
| DashboardUrl | `{StackName}-DashboardUrl` | CloudWatch dashboard URL |
| PassengersTableArn | `{StackName}-PassengersTableArn` | Conditional (HasPassengersTable) |

## Security

- Lambda: Per-function execution role with least-privilege policies
- IAM: Conditional DynamoDB policies scoped to `!GetAtt Table.Arn` — no wildcards
- API Gateway: JWT authorizer (Cognito), CORS locked to `AllowedOrigin` parameter (defaults to `https://none.invalid` — blocks cross-origin until post-deploy sets CloudFront domain), access logging
- DynamoDB: SSE enabled, PAY_PER_REQUEST billing
- CloudWatch: Log groups with 30-day retention
- ECR pull and CloudWatch PutMetricData use `Resource: '*'` (AWS API limitation — documented)

## Compose Config

Parameter overrides applied by `/ipa.compose`:

| Parameter | Value | Reason |
|-----------|-------|--------|
| FunctionName | fn | REST API handler |
| InvokeMode | RESPONSE_STREAM | SSE streaming support |
| Timeout | 300 | Long-running inference requests |
| EnablePassengersTable | true | Demo feature — Titanic dataset |

## Deploy Command

```bash
aws cloudformation deploy \
  --template-file infra/cfn/backend/backend.yml \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-backend \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Namespace=$(APP_NAMESPACE) \
    Environment=$(APP_ENV) \
    ImageUri=$(REPO_URI):$(IMAGE_TAG) \
    AuthIssuer=$(AUTH_ISSUER) \
    AuthAudience=$(AUTH_AUDIENCE) \
    EnablePassengersTable=true
```
