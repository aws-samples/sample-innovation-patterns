---
name: ipa-stack-logs
description: "Deploy a centralized S3 log bucket for CloudFront, S3 access, and VPC flow logs."
---

# ipa-stack-logs

Deploy a centralized S3 log bucket. Provides bucket name and ARN outputs for
downstream stacks that need log destinations (frontend CloudFront/S3 access logs).

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-logs` |
| Template | `infra/cfn/logs/logs.yml` |
| Capabilities | none |
| Lifecycle | prepare (prerequisite stack) |
| Tier | logs |

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars" |
| AccountId | String | — | `/^\d{12}$/` | "Must be 12-digit AWS account ID" |
| Region | String | — | `/^[a-z]{2}-[a-z]+-\d$/` | "Must be valid AWS region" |
| KmsKeyArn | String | *(empty)* | `/^(arn:aws:kms:[a-z0-9-]+:\d{12}:key\/[a-f0-9-]+)?$/` | "Invalid KMS key ARN" |

All parameters are **Configuration** type — sourced from `.env` or defaults.

## Wirable Parameters

No wirable parameters — all parameters are configuration type.

## Compose Config

No Compose Config prompts — all values come from `.env`.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| LogBucketName | S3 bucket name for log destinations | `{StackName}-LogBucketName` | ipa-stack-frontend (LogBucketDomainName) |
| LogBucketArn | S3 bucket ARN for IAM policy scoping | `{StackName}-LogBucketArn` | Security policy scoping |

## Feature Flags

None.

## Teardown Notes

CloudFormation cannot delete non-empty S3 buckets. If teardown fails, manually
empty the bucket first: `aws s3 rm s3://{bucket-name} --recursive` then re-run
`make -f scripts/prepare.mk teardown-logs`.

## Security Summary

**Required IAM actions**: s3:CreateBucket, DeleteBucket, PutBucketPolicy,
PutBucketVersioning, PutEncryptionConfiguration, PutLifecycleConfiguration,
PutBucketPublicAccessBlock, PutBucketOwnershipControls — scoped to
`arn:aws:s3:::{ns}-{env}-logs-*`
**Security controls**: Public access blocked, SSE-S3 (AES-256) encryption,
versioning enabled, 90-day lifecycle expiration, TLS-only access (DenyNonSSL),
bucket policy scoped to specific AWS service principals with SourceAccount condition
**Full advisory**: See [SECURITY.md](SECURITY.md)
