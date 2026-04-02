---
name: ipa-stack-dynamodb
description: "Deploy a DynamoDB table for data persistence."
---

# ipa.stack.dynamodb

Deploy a DynamoDB table with a configurable partition key. Provides TableArn and TableName outputs for downstream Lambda stacks and security policy scoping. Supports multi-instance deployment — one stack per data model (e.g., `ddb-passengers`, `ddb-jobs`).

## CloudFormation Contract

- **Template**: `infra/cfn/dynamodb/dynamodb.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-ddb` (single instance) or `{APP_NAMESPACE}-{APP_ENV}-ddb-{model}` (multi-instance)
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| TableName | String | — | `/^[a-z][a-z0-9-]{0,29}$/` | "Must be 1-30 chars, lowercase letters/digits/hyphens, starts with letter" |
| PartitionKey | String | `id` | — | — |
| BillingMode | String | `PAY_PER_REQUEST` | `PAY_PER_REQUEST \| PROVISIONED` | — |

**Configuration** parameters: Namespace, Environment (from `.env`). PartitionKey, BillingMode use template defaults unless overridden.
**Pattern-provided** parameter: TableName — sourced from `.env` via `APP_DDB_TABLE_{MODEL}` convention (e.g., `APP_DDB_TABLE_PASSENGERS=passengers`).

## Table Naming Convention

Physical DynamoDB table names are prefixed with namespace and environment: `{Namespace}_{Environment}_{TableName}` (underscores). The `TableName` parameter provides only the logical suffix — the template applies the prefix automatically.

Examples:
- Namespace=`app`, Environment=`dev`, TableName=`passengers` → `app_dev_passengers`
- Namespace=`myapp`, Environment=`stage`, TableName=`jobs` → `myapp_stage_jobs`

This ensures all tables in an account are scoped to their namespace and environment, preventing collisions across projects or environments.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| TableArn | DynamoDB table ARN for IAM policy scoping | `{StackName}-TableArn` | ipa.stack.lambda (fn + fn-stream) — DynamoDbTableArns parameter |

## Naming Convention

Physical DynamoDB table names follow a strict convention enforced by the CloudFormation template:

```
{Namespace}_{Environment}_{TableName}
```

Examples:
- `app_dev_passengers` (Namespace=app, Environment=dev, TableName=passengers)
- `myapp_stage_jobs` (Namespace=myapp, Environment=stage, TableName=jobs)

App-lib resolves table names by the same convention at runtime via `PynamodbUtil.env_table_name()`. No table name is passed as an environment variable to Lambda — the convention is the contract. The `TableArn` output is still exported for IAM policy scoping by downstream Lambda stacks.

## Security Summary

**Required IAM actions**: dynamodb:CreateTable, DeleteTable, DescribeTable, UpdateTable, TagResource, UntagResource — scoped to `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*`
**Security controls**: Encryption at rest (SSE, AWS-owned key), no public access, IAM-only
**Full advisory**: See [SECURITY.md](SECURITY.md)
