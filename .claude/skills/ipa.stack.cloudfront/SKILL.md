---
name: ipa-stack-cloudfront
description: "Deploy a CloudFront distribution serving static web content from S3 via OAC."
---

# ipa.stack.cloudfront

Deploy a CloudFront distribution fronting an S3 bucket via Origin Access Control (OAC). Serves a React SPA with client-side routing support (403/404 -> /index.html). Uses the default `*.cloudfront.net` domain. Provides AppUrl, DistributionId, and DistributionDomainName outputs for downstream consumers (post-deploy configure-frontend, invalidation).

## CloudFormation Contract

- **Template**: `infra/cfn/cloudfront/cloudfront.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-cf`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `^[a-z][a-z0-9-]{0,11}$` | Invalid namespace |
| Environment | String | — | `dev`, `staging`, `prod` | — |
| S3BucketName | String | — | — | — |
| S3BucketArn | String | — | — | — |
| S3BucketDomainName | String | — | — | — |
| LogBucketName | String | — | — | — |

### Parameter Classification

**Configuration** (2) — sourced from `.env`:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`

**Wirable — Required** (4) — sourced from upstream stack outputs:
- S3BucketName <- ipa.stack.s3 `BucketName`
- S3BucketArn <- ipa.stack.s3 `BucketArn`
- S3BucketDomainName <- ipa.stack.s3 `BucketDomainName`
- LogBucketName <- ipa.security `LogBucketName`

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| AppUrl | CloudFront URL (`https://{id}.cloudfront.net`) | `{StackName}-AppUrl` | post-deploy.mk configure-frontend (OIDC redirect), update-cognito-callback |
| DistributionId | Distribution ID | `{StackName}-DistributionId` | post-deploy.mk invalidate-cf |
| DistributionDomainName | CloudFront domain name | `{StackName}-DistributionDomainName` | Reference |

## Security Summary

**Required IAM actions**: cloudfront:CreateDistribution, UpdateDistribution, DeleteDistribution, GetDistribution, TagResource, CreateOriginAccessControl, DeleteOriginAccessControl + s3:PutBucketPolicy on S3 bucket — scoped to `{APP_NAMESPACE}-{APP_ENV}-*`
**Security controls**: OAC with SigV4 signing (no public S3 access), HTTPS-only viewer protocol, S3 bucket policy scoped to specific distribution ARN
**Known deferrals**: See [SECURITY.md](SECURITY.md)
**Full advisory**: See [SECURITY.md](SECURITY.md)
