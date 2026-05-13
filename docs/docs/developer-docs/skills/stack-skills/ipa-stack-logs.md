---
title: /ipa-stack-logs
sidebar_position: 4
---

# /ipa-stack-logs

Centralized S3 log bucket for CloudFront, S3 access, and VPC flow logs. A prepare-lifecycle stack that persists across deploy/destroy cycles.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-logs` |
| Template | `infra/cfn/logs/logs.yml` |
| Capabilities | None |
| Lifecycle | prepare |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Namespace` | *(from `.env`)* | Project namespace |
| `Environment` | *(from `.env`)* | Environment label |
| `AccountId` | *(from `.env`)* | 12-digit AWS account ID |
| `Region` | *(from `.env`)* | AWS region |
| `KmsKeyArn` | *(empty)* | Optional KMS key ARN for encryption (defaults to SSE-S3 AES-256) |

## Outputs

| Output | Description |
|--------|-------------|
| `LogBucketName` | S3 bucket name for log destinations |
| `LogBucketArn` | Bucket ARN for IAM policy scoping |

## Security

- All public access blocked (four-way Block Public Access)
- SSE-S3 (AES-256) encryption at rest
- Versioning enabled
- 90-day lifecycle expiration
- TLS-only access enforced (DenyNonSSL bucket policy)
- Bucket policy scoped to specific AWS service principals with `aws:SourceAccount` condition

## Wiring

Other stacks consume the log bucket output:

| Consumer | Parameter Wired |
|----------|----------------|
| Frontend | `LogBucketDomainName` ← `LogBucketName` (append `.s3.amazonaws.com`) |

## Teardown

CloudFormation cannot delete non-empty S3 buckets. If `teardown-logs` fails, empty the bucket manually:

```bash
aws s3 rm s3://{bucket-name} --recursive
make -f scripts/prepare.mk teardown-logs
```

## Related Skills

- [/ipa-prepare](../lifecycle-skills/ipa-prepare.md) — Deploys this stack
- [/ipa-stack-frontend](./ipa-stack-frontend.md) — Consumes log bucket for access logging
