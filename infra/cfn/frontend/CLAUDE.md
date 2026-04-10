# Frontend Tier — CloudFormation Template

**Template**: `infra/cfn/frontend/frontend.yml`
**Stack name**: `{APP_NAMESPACE}-{APP_ENV}-frontend`
**Capabilities**: None (no IAM resources)

## What This Template Does

Deploys a static web hosting tier: private S3 bucket + CloudFront distribution with OAC. All resources are always created (no feature flags).

## Parameters

| Parameter | Required | Default | Source |
|-----------|----------|---------|--------|
| Namespace | Yes | — | `.env` APP_NAMESPACE |
| Environment | Yes | — | `.env` APP_ENV |
| BucketNameSuffix | No | `web` | Pattern config |
| LogBucketDomainName | Yes | — | Security stack → `LogBucketName` + `.s3.amazonaws.com` |

## Outputs

| Output | Used By |
|--------|---------|
| AppUrl | Post-deploy: configure-frontend, Cognito callback URL |
| DistributionId | Post-deploy: cache invalidation |
| DistributionDomainName | Post-deploy: Cognito callback URL |
| BucketName | Post-deploy: S3 sync upload target |

## Post-Deploy Integration

After this stack deploys, the following post-deploy steps consume its outputs:

1. **configure-frontend** — generates `config.js` using `AppUrl` + backend `ApiUrl`
2. **upload-frontend** — `aws s3 sync web-client/dist/ s3://{BucketName}/ --delete`
3. **invalidate-cf** — `aws cloudfront create-invalidation --distribution-id {DistributionId}`
4. **update-cognito-callback** — adds `{AppUrl}/authentication/callback` to Cognito allowed URLs

## Internal Wiring

This consolidated template replaces the former `s3.yml` + `cloudfront.yml` cross-stack wiring with internal `!GetAtt` references:

- CloudFront origin → `!GetAtt WebBucket.RegionalDomainName` (was `S3BucketDomainName` parameter)
- BucketPolicy resource → `!Ref WebBucket` + `!GetAtt WebBucket.Arn` (was `S3BucketName`/`S3BucketArn` parameters)

## Security Properties

- S3: Block Public Access enabled, AES256 encryption, access logging to log bucket
- CloudFront: HTTPS-only (redirect), OAC (no OAI), TLSv1.2 minimum
- BucketPolicy: Scoped to CloudFront distribution ARN via OAC principal
