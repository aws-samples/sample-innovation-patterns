# Pattern: react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, HTTP API (v2) through API Gateway with JWT authorizer, Lambda compute with container images from ECR, DynamoDB for data storage, and Cognito for authentication. SSE streaming routes support a 5-minute integration timeout via HTTP API v2.

## Stack Sequence

1. ipa.stack.cognito (prepare) — Cognito User Pool for authentication
   - Depends on: none
   - Suffix: cognito

2. ipa.stack.ecr (prepare) — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

3. ipa.stack.dynamodb — DynamoDB table for data persistence
   - Depends on: none
   - Suffix: ddb-passengers

4. ipa.stack.lambda — Lambda function for all routes (buffered + streaming)
   - Depends on: ipa.stack.ecr, ipa.stack.cognito, ipa.stack.dynamodb
   - Suffix: fn
   - Config: FunctionName=fn InvokeMode=RESPONSE_STREAM Timeout=300

5. ipa.stack.apigwv2 — HTTP API (v2) with JWT authorizer and SSE streaming
   - Depends on: ipa.stack.lambda (fn), ipa.stack.cognito
   - Suffix: apigwv2

5a. ipa.stack.app-cloudwatch — CloudWatch dashboard, metric filters, and alarms
   - Depends on: ipa.stack.lambda (fn), ipa.stack.apigwv2
   - Suffix: app-cloudwatch

6. ipa.stack.s3 — S3 bucket for static web hosting
   - Depends on: none
   - Suffix: s3

7. ipa.stack.cloudfront — CloudFront distribution fronting S3
   - Depends on: ipa.stack.s3
   - Suffix: cf

## Teardown Sequence

1. ipa.stack.cloudfront (suffix: cf)
2. ipa.stack.s3 (suffix: s3)
2a. ipa.stack.app-cloudwatch (suffix: app-cloudwatch)
3. ipa.stack.apigwv2 (suffix: apigwv2)
4. ipa.stack.lambda fn (suffix: fn)
5. ipa.stack.dynamodb (suffix: ddb-passengers)

## Wiring

```yaml
wiring:
  # ECR → Lambda (fn) — container image
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: fn
      parameter: ImageUri
    notes: "Container image URI — compose appends :$(IMAGE_TAG) (resolved from scripts/util/version.py at build/deploy time)"

  # DynamoDB → Lambda (fn) — table ARN for IAM policy
  - source:
      stack: ddb-passengers
      output: TableArn
    target:
      stack: fn
      parameter: DynamoDbTableArns
    notes: "DynamoDB table ARN for Lambda execution role IAM policy"

  # Cognito → Lambda (fn) — OIDC issuer for JWT validation
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: fn
      parameter: AuthIssuer
    notes: "Cognito OIDC issuer URL → AUTH_ISSUER env var for JWT validation"

  # Cognito → Lambda (fn) — client ID for JWT audience
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: fn
      parameter: AuthAudience
    notes: "Cognito app client ID → AUTH_AUDIENCE env var for JWT audience validation"

  # Lambda (fn) → API Gateway v2 — function ARN for all routes
  - source:
      stack: fn
      output: FunctionArn
    target:
      stack: apigwv2
      parameter: LambdaFunctionArn
    notes: "Single Lambda handles buffered + streaming routes"

  # Cognito → API Gateway v2 — issuer URL for JWT authorizer
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: apigwv2
      parameter: IssuerUrl
    notes: "Cognito OIDC issuer URL for JWT authorizer validation"

  # Cognito → API Gateway v2 — client ID for JWT audience
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: apigwv2
      parameter: UserPoolClientId
    notes: "Cognito app client ID for JWT audience validation"

  # S3 → CloudFront — bucket domain name for origin
  - source:
      stack: s3
      output: BucketDomainName
    target:
      stack: cf
      parameter: S3BucketDomainName
    notes: "S3 regional domain name for CloudFront origin configuration"

  # S3 → CloudFront — bucket ARN for OAC policy
  - source:
      stack: s3
      output: BucketArn
    target:
      stack: cf
      parameter: S3BucketArn
    notes: "S3 bucket ARN for CloudFront OAC bucket policy condition"

  # S3 → CloudFront — bucket name for bucket policy
  - source:
      stack: s3
      output: BucketName
    target:
      stack: cf
      parameter: S3BucketName
    notes: "S3 bucket name for CloudFront OAC bucket policy resource"

  # Lambda → App CloudWatch — no explicit wiring needed
  # App CloudWatch constructs log group names by convention from Namespace + Environment
  # Override with LambdaLogGroupName/ApiGatewayLogGroupName parameters if needed
```

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| APIGW-1 | CORS origin `*` during initial deploy window | CloudFront domain unknown at API deploy time; auto-wired in post-deploy |
| S3-1 | No bucket versioning | POC scope |
| CF-1 | No custom domain / ACM certificate | POC uses *.cloudfront.net |
| CF-2 | No WAF | POC scope + HTTP API v2 does not support WAF |
| CF-3 | PriceClass_100 only | POC — US/Canada/Europe only |
| CF-4 | Short DefaultTTL (300s) | POC — production should tune per content type |

## Post-Deploy

Steps that run after all stacks are successfully deployed. These are operational
steps (not CloudFormation stacks) that wire deployed infrastructure together.
Post-deploy runs automatically within /ipa.deploy — no separate invocation needed.

### load-data
- Action: Load sample Titanic passenger data from CSV into DynamoDB table
- Script: `cd app-lib && uv run python -m app_lib.util.load_dynamodb_util`
- Depends on: (none within post-deploy)
- Notes: Uses PutItem (upsert) — safe to re-run. Reads from app-lib/src/app_lib/assets/datasets/titanic/walkthrough_titanic.csv

### configure-frontend
- Action: Generate web-client/dist/config.js with runtime configuration
- Script: scripts/util/configure_frontend.py
- Depends on: (none within post-deploy)
- Stack outputs:
  - apigwv2 → ApiUrl
  - cf → AppUrl
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_END_SESSION_ENDPOINT

### upload-frontend
- Action: Sync web-client/dist/ to S3 bucket
- Depends on: configure-frontend
- Stack outputs:
  - s3 → BucketName
- Command: aws s3 sync web-client/dist/ s3://{BucketName}/ --delete

### invalidate-cf
- Action: Create CloudFront cache invalidation and wait for completion
- Depends on: upload-frontend
- Stack outputs:
  - cf → DistributionId
- Command: aws cloudfront create-invalidation + aws cloudfront wait invalidation-completed

### update-cognito-callback
- Action: Update Cognito callback/logout URLs — add CloudFront domain alongside localhost
- Depends on: invalidate-cf
- Stack outputs:
  - cf → AppUrl
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID (for reference — not directly used by this target)
- Command: aws cloudformation deploy (Cognito stack with CallbackURL={AppUrl}/authentication/callback)
- Notes: Passes ALL original prepare-cognito parameters plus updated CallbackURL.
  The localhost callback remains — CloudFront URL is added as additional allowed callback.

### update-apigwv2-cors
- Action: Update API Gateway v2 CORS origin with CloudFront domain
- Depends on: update-cognito-callback
- Stack outputs:
  - cf → AppUrl
  - fn → FunctionArn
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID
- Command: aws cloudformation deploy (apigwv2 stack with updated AllowedOrigin parameter)
- Notes: Must pass ALL original deploy-apigwv2 parameters plus AllowedOrigin={AppUrl}
