# Pattern: react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, REST API through API Gateway, Lambda compute with container images from ECR, DynamoDB for data storage, and Cognito for authentication.

## Stack Sequence

1. ipa.stack.ecr (prepare) — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

2. ipa.stack.cognito — Cognito User Pool for authentication
   - Depends on: none
   - Suffix: cognito

3. ipa.stack.dynamodb — DynamoDB table for data persistence
   - Depends on: none
   - Suffix: ddb

4. ipa.stack.lambda — Buffered Lambda function for REST requests
   - Depends on: ipa.stack.ecr, ipa.stack.cognito, ipa.stack.dynamodb
   - Suffix: fn
   - Config: FunctionName=fn InvokeMode=BUFFERED

5. ipa.stack.lambda — Streaming Lambda function for real-time responses
   - Depends on: ipa.stack.ecr, ipa.stack.cognito, ipa.stack.dynamodb
   - Suffix: fn-stream
   - Config: FunctionName=fn-stream InvokeMode=RESPONSE_STREAM

6. ipa.stack.apigw — API Gateway REST API with Cognito authorizer
   - Depends on: ipa.stack.lambda (fn), ipa.stack.lambda (fn-stream), ipa.stack.cognito
   - Suffix: apigw

## Teardown Sequence

1. ipa.stack.apigw (suffix: apigw)
2. ipa.stack.lambda fn-stream (suffix: fn-stream)
3. ipa.stack.lambda fn (suffix: fn)
4. ipa.stack.dynamodb (suffix: ddb)
5. ipa.stack.cognito (suffix: cognito)

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

  # ECR → Lambda (fn-stream) — container image
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: fn-stream
      parameter: ImageUri
    notes: "Container image URI for streaming Lambda function (compose appends :$(IMAGE_TAG))"

  # DynamoDB → Lambda (fn) — table ARN for IAM policy
  - source:
      stack: ddb
      output: TableArn
    target:
      stack: fn
      parameter: DynamoDbTableArns
    notes: "DynamoDB table ARN for Lambda execution role IAM policy"

  # DynamoDB → Lambda (fn-stream) — table ARN for IAM policy
  - source:
      stack: ddb
      output: TableArn
    target:
      stack: fn-stream
      parameter: DynamoDbTableArns
    notes: "DynamoDB table ARN for Lambda execution role IAM policy"

  # DynamoDB → Lambda (fn) — table name for runtime env var
  - source:
      stack: ddb
      output: TableName
    target:
      stack: fn
      parameter: TableName
    notes: "DynamoDB table name → TABLE_NAME env var for runtime data access"

  # DynamoDB → Lambda (fn-stream) — table name for runtime env var
  - source:
      stack: ddb
      output: TableName
    target:
      stack: fn-stream
      parameter: TableName
    notes: "DynamoDB table name → TABLE_NAME env var for runtime data access"

  # Cognito → Lambda (fn) — OIDC issuer for JWT validation
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: fn
      parameter: AuthIssuer
    notes: "Cognito OIDC issuer URL → AUTH_ISSUER env var for JWT validation"

  # Cognito → Lambda (fn-stream) — OIDC issuer for JWT validation
  - source:
      stack: cognito
      output: IssuerUrl
    target:
      stack: fn-stream
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

  # Cognito → Lambda (fn-stream) — client ID for JWT audience
  - source:
      stack: cognito
      output: UserPoolClientId
    target:
      stack: fn-stream
      parameter: AuthAudience
    notes: "Cognito app client ID → AUTH_AUDIENCE env var for JWT audience validation"

  # Lambda (fn) → API Gateway — buffered Lambda ARN
  - source:
      stack: fn
      output: FunctionArn
    target:
      stack: apigw
      parameter: LambdaFunctionArn
    notes: "Buffered Lambda function ARN for /{proxy+} routes"

  # Lambda (fn-stream) → API Gateway — streaming Lambda ARN
  - source:
      stack: fn-stream
      output: FunctionArn
    target:
      stack: apigw
      parameter: StreamingLambdaFunctionArn
    notes: "Streaming Lambda function ARN for /api/v1/sse/{proxy+} routes"

  # Cognito → API Gateway — User Pool ARN for authorizer
  - source:
      stack: cognito
      output: UserPoolArn
    target:
      stack: apigw
      parameter: UserPoolArn
    notes: "Cognito User Pool ARN for COGNITO_USER_POOLS authorizer"
```

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| APIGW-1 | CORS Access-Control-Allow-Origin: * | POC scope — production should scope to CloudFront domain |
| APIGW-2 | REST API 29s integration timeout | REST API limitation — HTTP API (v2) needed for production long-polling SSE |

## Post-Deploy

Steps that run after all stacks are successfully deployed. These are operational
steps (not CloudFormation stacks) that wire deployed infrastructure together.
Post-deploy runs automatically within /ipa.deploy — no separate invocation needed.

### configure-frontend
- Action: Generate web-client/dist/config.js with runtime configuration
- Script: scripts/util/configure_frontend.py
- Depends on: (none within post-deploy)
- Stack outputs:
  - apigw → ApiUrl
  - cf → AppUrl
  - cognito → IssuerUrl, UserPoolClientId, EndSessionEndpoint

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
- Action: Update Cognito callback/logout URLs with CloudFront domain
- Depends on: invalidate-cf
- Stack outputs:
  - cf → AppUrl
- Command: aws cloudformation deploy (Cognito stack with updated CallbackURL parameter)
- Notes: Must pass ALL original deploy-cognito parameters plus CallbackURL={AppUrl}/authentication/callback
