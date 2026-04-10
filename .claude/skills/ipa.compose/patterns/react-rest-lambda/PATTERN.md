# Pattern: react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, HTTP API (v2) through API Gateway with JWT authorizer, Lambda compute with container images from ECR, DynamoDB for data storage (feature-flagged), CloudWatch observability, and Cognito for authentication. Uses consolidated tier-based stacks.

## Stack Sequence

1. ipa.stack.cognito (prepare) — Cognito User Pool for authentication
   - Depends on: none
   - Suffix: cognito

2. ipa.stack.ecr (prepare) — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

3. ipa.stack.backend — Backend tier: Lambda + API Gateway v2 + DynamoDB (feature-flagged) + CloudWatch
   - Depends on: ipa.stack.ecr, ipa.stack.cognito
   - Suffix: backend
   - Config: FunctionName=fn InvokeMode=RESPONSE_STREAM Timeout=300 EnablePassengersTable=true

4. ipa.stack.frontend — Frontend tier: S3 + CloudFront + OAC
   - Depends on: none (Security stack provides LogBucketDomainName)
   - Suffix: frontend

## Teardown Sequence

1. ipa.stack.frontend (suffix: frontend)
2. ipa.stack.backend (suffix: backend)

## Wiring

```yaml
wiring:
  # ECR → Backend — container image
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: backend
      parameter: ImageUri
    notes: "Container image URI — compose appends :$(IMAGE_TAG) (resolved from scripts/util/version.py at build/deploy time)"

  # Cognito → Backend — OIDC issuer for JWT validation
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: backend
      parameter: AuthIssuer
    notes: "Cognito OIDC issuer URL → AuthIssuer parameter and AUTH_ISSUER env var"

  # Cognito → Backend — client ID for JWT audience
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: backend
      parameter: AuthAudience
    notes: "Cognito app client ID → AuthAudience parameter and AUTH_AUDIENCE env var"

  # Security → Frontend — log bucket for access logs
  - source:
      stack: security
      output: LogBucketName
    target:
      stack: frontend
      parameter: LogBucketDomainName
    notes: "Log bucket domain name — compose appends .s3.amazonaws.com to LogBucketName output"
```

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| S3-1 | No bucket versioning | POC scope |
| CF-1 | No custom domain / ACM certificate | POC uses *.cloudfront.net |
| CF-2 | No WAF | POC scope + HTTP API v2 does not support WAF |
| CF-3 | PriceClass_100 only | POC — US/Canada/Europe only |
| CF-4 | Short DefaultTTL (300s) | POC — production should tune per content type |
| APIGW-1 | CORS origin `*` during initial deploy | CloudFront domain unknown at API deploy time; auto-wired in post-deploy |

## Post-Deploy

Steps that run after all stacks are successfully deployed. These are operational
steps (not CloudFormation stacks) that wire deployed infrastructure together.
Post-deploy runs automatically within /ipa.deploy — no separate invocation needed.

### load-data
- Action: Load sample Titanic passenger data from CSV into DynamoDB table
- Script: `cd app-lib && uv run python -m app_lib.features.passengers.util.load_dynamodb_util`
- Depends on: (none within post-deploy)
- Notes: Uses PutItem (upsert) — safe to re-run. Reads from app-lib/src/app_lib/assets/datasets/titanic/walkthrough_titanic.csv

### configure-frontend
- Action: Generate web-client/dist/config.js with runtime configuration
- Script: scripts/util/configure_frontend.py
- Depends on: (none within post-deploy)
- Stack outputs:
  - backend → ApiUrl
  - frontend → AppUrl
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_END_SESSION_ENDPOINT

### upload-frontend
- Action: Sync web-client/dist/ to S3 bucket
- Depends on: configure-frontend
- Stack outputs:
  - frontend → BucketName
- Command: aws s3 sync web-client/dist/ s3://{BucketName}/ --delete

### invalidate-cf
- Action: Create CloudFront cache invalidation and wait for completion
- Depends on: upload-frontend
- Stack outputs:
  - frontend → DistributionId
- Command: aws cloudfront create-invalidation + aws cloudfront wait invalidation-completed

### update-cognito-callback
- Action: Update Cognito callback/logout URLs — add CloudFront domain alongside localhost
- Depends on: invalidate-cf
- Stack outputs:
  - frontend → AppUrl
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID (for reference — not directly used by this target)
- Command: aws cloudformation deploy (Cognito stack with CallbackURL={AppUrl}/authentication/callback)
- Notes: Passes ALL original prepare-cognito parameters plus updated CallbackURL.
  The localhost callback remains — CloudFront URL is added as additional allowed callback.

### update-backend-cors
- Action: Update API Gateway v2 CORS origin with CloudFront domain
- Depends on: update-cognito-callback
- Stack outputs:
  - frontend → AppUrl
- Notes: Re-deploys backend stack with AllowedOrigin set to CloudFront URL.
  Must pass ALL original deploy-backend parameters plus updated frontend AppUrl for CORS.
