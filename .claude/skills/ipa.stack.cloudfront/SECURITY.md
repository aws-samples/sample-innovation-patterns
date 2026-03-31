# Security Advisory: ipa.stack.cloudfront

## Deployment Permissions

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| cloudfront:CreateDistribution | `*` (CloudFront is global) | Create distribution |
| cloudfront:UpdateDistribution | `arn:aws:cloudfront::{account}:distribution/*` | Update distribution config |
| cloudfront:DeleteDistribution | `arn:aws:cloudfront::{account}:distribution/*` | Stack teardown |
| cloudfront:GetDistribution | `arn:aws:cloudfront::{account}:distribution/*` | Read state |
| cloudfront:TagResource | `arn:aws:cloudfront::{account}:distribution/*` | Apply tags |
| cloudfront:CreateOriginAccessControl | `*` | Create OAC |
| cloudfront:DeleteOriginAccessControl | `*` | Stack teardown |
| s3:PutBucketPolicy | `arn:aws:s3:::{ns}-{env}-web-*` | Grant OAC read access |

Note: CloudFront `Create*` actions require `Resource: *` — this is an AWS limitation, not a policy choice.

## Runtime Permissions

Advisory — permissions exercised by CloudFront at request time:

| Action | Resource Scope | Granted To | Purpose |
|--------|---------------|------------|---------|
| s3:GetObject | `arn:aws:s3:::{bucket}/*` | CloudFront OAC | Serve static assets to viewers |

## Security Controls

| Control | Implementation |
|---------|---------------|
| OAC with SigV4 | Origin access uses IAM signing — no public S3 URL |
| HTTPS only | `ViewerProtocolPolicy: redirect-to-https` |
| Bucket policy scoping | `Condition.StringEquals.AWS:SourceArn` limits access to this specific distribution |
| No custom headers exposed | Only standard CloudFront response headers |

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| CF-1 | No custom domain / ACM certificate | POC uses `*.cloudfront.net` — production should add custom domain with ACM cert |
| CF-2 | No WAF | POC scope — production should add WAF for DDoS/bot protection |
| CF-3 | PriceClass_100 (US/Canada/Europe only) | POC scope — production may need PriceClass_All for global coverage |
| CF-4 | Short DefaultTTL (300s) | Simplified for POC — production should tune per content type |
| CF-5 | No access logging | POC scope — production should enable access logging to S3 |
