---
name: ipa-stack-tfstate
description: "Deploy a Terraform state backend (S3 + DynamoDB) via CloudFormation."
---

# ipa-stack-tfstate

Deploy the Terraform state backend infrastructure. This stack is always deployed via CloudFormation — even when `APP_IAC=terraform` — because the Terraform state backend must exist before Terraform can run.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-tfstate` |
| Template | `infra/cfn/tfstate/tfstate.yml` |
| Capabilities | none |
| Lifecycle | prepare (prerequisite stack) |
| Tier | tfstate |

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |

All parameters are **Configuration** type — sourced from `.env`.

## Wirable Parameters

No wirable parameters — all parameters are configuration type.

## Compose Config

No Compose Config prompts — all values come from `.env`.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| StateBucketName | S3 bucket name for Terraform state files | `{StackName}-StateBucketName` | All Terraform modules (backend config) |
| LockTableName | DynamoDB table name for state locking | `{StackName}-LockTableName` | All Terraform modules (backend config) |

## Feature Flags

None.

## Teardown Notes

Both the S3 bucket and DynamoDB table have `DeletionPolicy: Retain`. Manual cleanup required:
1. Empty the S3 bucket: `aws s3 rm s3://{bucket-name} --recursive`
2. Delete the DynamoDB table: `aws dynamodb delete-table --table-name {table-name}`
3. Delete the bucket: `aws s3 rb s3://{bucket-name}`
4. Then re-run teardown: `make -f scripts/prepare.mk teardown-tfstate`

## Security Summary

**Required IAM actions**: s3:CreateBucket, PutBucketVersioning, PutBucketEncryption, PutBucketPublicAccessBlock, PutBucketPolicy — scoped to `arn:aws:s3:::{ns}-{env}-tfstate-*`. dynamodb:CreateTable, DescribeTable, UpdateTable, UpdateContinuousBackups — scoped to `arn:aws:dynamodb:{Region}:{AccountId}:table/{ns}_{env}_tfstate_lock`.
**Security controls**: S3 versioning enabled, AES256 encryption, public access blocked, TLS-only policy. DynamoDB SSE enabled, PITR enabled, PAY_PER_REQUEST billing.
**Full advisory**: See [SECURITY.md](SECURITY.md)
