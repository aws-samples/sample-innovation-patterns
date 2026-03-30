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

## Teardown Sequence

1. ipa.stack.lambda fn-stream (suffix: fn-stream)
2. ipa.stack.lambda fn (suffix: fn)
3. ipa.stack.dynamodb (suffix: ddb)
4. ipa.stack.cognito (suffix: cognito)

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
    notes: "Container image URI for buffered Lambda function (compose appends :$(IMAGE_TAG))"

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
```

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| (none yet) | | |
