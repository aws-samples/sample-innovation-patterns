# Architecture: react-rest-lambda Pattern

Full-stack serverless web application deployed as composable CloudFormation stacks.

## System Architecture

```text
Layer 3:  [CloudFront] ──▶ S3 (static), API Gateway (dynamic)
Layer 2:  [API Gateway] ──▶ Lambda (fn), Lambda (fn-stream), Cognito (authorizer)
Layer 1:  [Lambda fn]   ──▶ ECR (image), DynamoDB (data), Cognito (JWT validation)
          [Lambda fn-stream] ──▶ ECR (image), DynamoDB (streams)
Layer 0:  [ECR]  [DynamoDB (ddb-passengers)]  [Cognito]  [S3]
```

## Stack Inventory

| Stack | Layer | Purpose | Status |
|-------|-------|---------|--------|
| ipa.stack.ecr | 0 | Container image repository | **Implemented** |
| ipa.stack.dynamodb | 0 | Data storage with streams | **Implemented** |
| ipa.stack.cognito | 0 | Authentication (User Pool, OAuth 2.0) | **Implemented** |
| ipa.stack.s3 | 0 | Static asset hosting | Pending (Spec 6) |
| ipa.stack.lambda-fn | 1 | Buffered request handler | **Implemented** |
| ipa.stack.lambda-fn-stream | 1 | Streaming response handler | **Implemented** |
| ipa.stack.apigw | 2 | REST API with Cognito authorizer | Pending (Spec 5) |
| ipa.stack.cloudfront | 3 | CDN distribution | Pending (Spec 7) |

## Deployment Order

Stacks deploy bottom-up (Layer 0 → 3). Within a layer, stacks have no mutual dependencies and can deploy in parallel. Teardown is reverse order (Layer 3 → 0).

**Current state**: Layer 0 stacks (ECR, DynamoDB, Cognito) and Layer 1 stacks (Lambda fn, Lambda fn-stream) are implemented. The pattern grows incrementally — each spec adds one or more stacks and the pattern remains deployable at every step.

## Security Model

- **No wildcard IAM ARNs** — all permissions scoped to specific resource ARNs
- **ecr:GetAuthorizationToken** and **ecr:BatchGetImage/GetDownloadUrlForLayer** are exceptions (AWS API limitations — documented in Lambda SECURITY.md)
- **Each stack owns its own IAM** — no cross-stack IAM references (composability principle)
- **No public resources** by default — all repositories and buckets are private
- **Manual teardown** for stateful resources — prevents accidental data loss

## Deployment Assumptions

- AWS credentials configured with Builder Execution Role permissions
- `.env` file with `APP_NAMESPACE` and `APP_ENV` set
- `uv` installed for execution layer commands
- `/ipa.compose` generates Makefiles and runbook from this pattern
- Single-environment POC scope (no multi-account or multi-region)
