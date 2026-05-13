---
name: ipa-stack-frontend
description: "Deploy a frontend tier stack: S3 static hosting + CloudFront distribution + OAC."
model: opus
---

# ipa-stack-frontend

Deploy a frontend tier stack: S3 static hosting + CloudFront distribution + OAC.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-frontend` |
| Template | `infra/cfn/frontend/frontend.yml` |
| Capabilities | None |
| Lifecycle | deploy (solution stack) |
| Tier | frontend |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Namespace | Yes | — | Project namespace prefix |
| Environment | Yes | — | Deployment environment (dev/staging/prod) |
| BucketNameSuffix | No | `web` | Suffix for S3 bucket name |
| LogBucketDomainName | Yes | — | Log bucket domain name for access logs |

## Wirable Parameters

Parameters that receive values from other stacks during composition:

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| LogBucketDomainName | logs | LogBucketName | Append `.s3.amazonaws.com` to output value |

## Outputs

| Output | Export Name | Description |
|--------|------------|-------------|
| AppUrl | `{StackName}-AppUrl` | CloudFront HTTPS URL |
| DistributionId | `{StackName}-DistributionId` | For cache invalidation |
| DistributionDomainName | `{StackName}-DistributionDomainName` | CloudFront domain |
| BucketName | `{StackName}-BucketName` | S3 bucket for upload |

## Build Requirements

| Type | Suffix | Dockerfile | Description |
|------|--------|------------|-------------|
| frontend | frontend | — | Build the React SPA in `web-client/` via `npm ci && npm run build`. Note: this project's frontend directory is `web-client`, not the default `frontend` — the generated `build-frontend` target must `cd web-client`, not `cd frontend`. |

## Feature Flags

None — frontend tier has no conditional resources.

## Security

- S3: Block Public Access, AES256 encryption, access logging
- CloudFront: HTTPS-only, OAC (sigv4), TLSv1.2_2021
- BucketPolicy scoped to distribution ARN
- No IAM roles (no CAPABILITY_NAMED_IAM needed)

## Deploy Command

```bash
aws cloudformation deploy \
  --template-file infra/cfn/frontend/frontend.yml \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-frontend \
  --parameter-overrides \
    Namespace=$(APP_NAMESPACE) \
    Environment=$(APP_ENV) \
    BucketNameSuffix=web \
    LogBucketDomainName=$(LOG_BUCKET_DOMAIN_NAME)
```
