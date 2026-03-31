---
name: ipa-stack-s3
description: "Deploy a private S3 bucket for static web hosting via CloudFront OAC."
---

# ipa.stack.s3

Deploy a private S3 bucket for static web hosting. The bucket is not publicly accessible — CloudFront accesses it via Origin Access Control (OAC). Hosts the React+Vite build output (`web-client/dist/`). Provides BucketName, BucketArn, and BucketDomainName outputs for downstream consumers (CloudFront, post-deploy upload).

## CloudFormation Contract

- **Template**: `infra/cfn/s3/s3.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-s3`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `^[a-z][a-z0-9-]{0,11}$` | Invalid namespace |
| Environment | String | — | `dev`, `staging`, `prod` | — |
| BucketNameSuffix | String | `web` | — | — |
| LogBucketName | String | — | — | — |

### Parameter Classification

**Configuration** (3) — sourced from `.env` or defaults:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`
- BucketNameSuffix — hardcoded default `web`

**Wirable — Required** (1) — sourced from upstream stack outputs:
- LogBucketName <- ipa.security `LogBucketName`

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| BucketName | S3 bucket name | `{StackName}-BucketName` | post-deploy.mk upload-frontend (S3 sync target) |
| BucketArn | S3 bucket ARN | `{StackName}-BucketArn` | ipa.stack.cloudfront (OAC policy scoping) |
| BucketDomainName | S3 regional domain name | `{StackName}-BucketDomainName` | ipa.stack.cloudfront (S3 origin) |

## Security Summary

**Required IAM actions**: s3:CreateBucket, PutBucketEncryption, PutBucketPolicy, PutPublicAccessBlock, DeleteBucket, PutBucketTagging — scoped to `{APP_NAMESPACE}-{APP_ENV}-web-*`
**Security controls**: All public access blocked, SSE-S3 encryption at rest, no static website hosting (OAC-only)
**Known deferrals**: See [SECURITY.md](SECURITY.md)
**Full advisory**: See [SECURITY.md](SECURITY.md)
