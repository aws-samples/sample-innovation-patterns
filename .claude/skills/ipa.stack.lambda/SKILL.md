---
name: ipa-stack-lambda
description: "Deploy a Lambda function with container image from ECR, optional DynamoDB access, Bedrock access, and Cognito JWT validation."
---

# ipa.stack.lambda

Deploy a Lambda function with container image packaging. One template deployed as multiple instances with different suffixes and InvokeMode values (e.g., `fn` for buffered REST, `fn-stream` for streaming). Provides FunctionArn and FunctionName outputs for downstream API Gateway integration.

## CloudFormation Contract

- **Template**: `infra/cfn/lambda/lambda.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-{suffix}` (suffix varies per instance — e.g., `fn`, `fn-stream`)
- **Capabilities**: `CAPABILITY_NAMED_IAM` (creates IAM execution role)

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
| FunctionName | String | — | `/^[a-z][a-z0-9-]{0,23}$/` | "Must be 1-24 chars, lowercase alphanumeric + hyphens, starts with letter" |
| InvokeMode | String | BUFFERED | `BUFFERED \| RESPONSE_STREAM` | "Must be BUFFERED or RESPONSE_STREAM" |
| MemorySize | Number | 512 | `128-10240` | "Must be between 128 and 10240 MB" |
| Timeout | Number | 30 | `1-900` | "Must be between 1 and 900 seconds" |
| LogBucketName | String | (empty) | — | — |
| ImageUri | String | — | — | — |
| AuthIssuer | String | — | — | — |
| AuthAudience | String | — | — | — |
| DynamoDbTableArns | String | (empty) | — | — |
| TableName | String | (empty) | — | — |

### Parameter Classification

**Configuration** (7) — sourced from `.env`, `Config:` annotations, or defaults:
- Namespace, Environment, FunctionName, InvokeMode, MemorySize, Timeout, LogBucketName

**Wirable — Required** (3) — sourced from upstream stack outputs:
- ImageUri ← ipa.stack.ecr `RepositoryUri` (compose appends `:$(IMAGE_TAG)`, resolved from `scripts/util/version.py`)
- AuthIssuer ← ipa.stack.cognito `IssuerUrl`
- AuthAudience ← ipa.stack.cognito `UserPoolClientId`

**Wirable — Optional** (2) — sourced from upstream stack outputs when DynamoDB is composed:
- DynamoDbTableArns ← ipa.stack.dynamodb `TableArn` (defaults to empty — no DynamoDB permissions granted)
- TableName ← ipa.stack.dynamodb `TableName` (defaults to empty — TABLE_NAME env var is empty)

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| FunctionArn | Lambda function ARN | `{StackName}-FunctionArn` | ipa.stack.apigw (integration target) |
| FunctionName | Lambda function name | `{StackName}-FunctionName` | Monitoring, invoke commands |
| ExecutionRoleArn | Lambda execution role ARN | `{StackName}-ExecutionRoleArn` | Security auditing |

## Build Requirements

This stack requires a container image in ECR before deployment.

| Type | Suffix | Description |
|------|--------|-------------|
| container | fn | Docker image built and pushed to ECR via `build.mk` target using `scripts/util/docker.mk` helpers |

Both `fn` and `fn-stream` instances use the same container image — one `build-fn` target suffices.

## Security Summary

**Required IAM actions**: lambda:CreateFunction, UpdateFunctionCode, UpdateFunctionConfiguration, DeleteFunction, GetFunction, TagResource, UntagResource + iam:CreateRole, PutRolePolicy, DeleteRole, PassRole — scoped to `{APP_NAMESPACE}-{APP_ENV}-*`
**Runtime permissions**: Conditional DynamoDB CRUD, ECR image pull, CloudWatch Logs, Bedrock invoke (always)
**Security controls**: No public function URL, dedicated least-privilege execution role, encryption in transit, 30-day log retention
**Full advisory**: See [SECURITY.md](SECURITY.md)
