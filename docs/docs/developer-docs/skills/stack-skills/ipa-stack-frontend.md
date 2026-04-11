---
title: /ipa.stack.frontend
sidebar_position: 7
---

# /ipa.stack.frontend

Frontend tier stack: S3 static hosting with CloudFront distribution and Origin Access Control (OAC).

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-frontend` |
| Template | `infra/cfn/frontend/frontend.yml` |
| Capabilities | None |
| Lifecycle | deploy |

## Parameters

### Wirable Parameters

| Parameter | Source | Required |
|-----------|--------|----------|
| `LogBucketDomainName` | security.LogBucketName | Yes |

### Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BucketNameSuffix` | `web` | Suffix for the S3 bucket name |

## Outputs

| Output | Description |
|--------|-------------|
| `AppUrl` | CloudFront HTTPS URL |
| `DistributionId` | CloudFront distribution ID (for cache invalidation) |
| `DistributionDomainName` | CloudFront domain name |
| `BucketName` | S3 bucket name (for uploading frontend assets) |

## Security

- S3 Block Public Access: enabled on all settings
- Encryption: AES-256 at rest
- CloudFront: HTTPS-only with TLSv1.2 minimum
- Origin Access Control: OAC with SigV4 signing (no legacy OAI)

## Post-Deploy Operations

After deployment, `scripts/post-deploy.mk` performs:

1. Generates `web-client/public/config.json` with API URL and auth endpoints
2. Builds the frontend (`npm run build` in `web-client/`)
3. Uploads build artifacts to the S3 bucket
4. Invalidates the CloudFront cache

## Related Skills

- [/ipa.security](../ipa-security.md) — Provides the log bucket for CloudFront access logs
- [/ipa.stack.backend](./ipa-stack-backend.md) — Provides the API URL for frontend configuration
- [/ipa.compose](../ipa-compose.md) — Assembles this stack into deployment patterns
