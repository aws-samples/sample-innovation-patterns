---
name: ipa-stack-apigw
description: "Deploy an API Gateway REST API fronting Lambda with Cognito authorizer, buffered and optional SSE streaming routes."
---

# ipa.stack.apigw

Deploy an API Gateway REST API with Cognito User Pool authorizer. Routes buffered traffic (`/{proxy+}`) to one Lambda and streaming traffic (`/api/v1/sse/{proxy+}`) to another. Streaming routes are optional — only created when `StreamingLambdaFunctionArn` is provided. Provides ApiUrl output for downstream consumers (configure-frontend, CloudFront).

## CloudFormation Contract

- **Template**: `infra/cfn/apigateway/apigateway.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-apigw`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| ApiName | String | — | — | — |
| StageName | String | `prod` | — | — |
| LambdaFunctionArn | String | — | — | — |
| StreamingLambdaFunctionArn | String | `''` | — | — |
| UserPoolArn | String | — | — | — |
| ThrottlingRateLimit | Number | `1000` | — | — |
| ThrottlingBurstLimit | Number | `500` | — | — |
| DeploymentHash | String | `initial` | — | — |

### Parameter Classification

**Configuration** (4) — sourced from `.env`, defaults, or auto-generated:
- ApiName — passed from Makefile as `$(APP_NAMESPACE)-$(APP_ENV)-api`
- StageName — hardcoded default `prod`
- ThrottlingRateLimit, ThrottlingBurstLimit — hardcoded defaults `1000`/`500`
- DeploymentHash — auto-generated at deploy time via `$(shell date +%s)` in Makefile

**Wirable — Required** (2) — sourced from upstream stack outputs:
- LambdaFunctionArn ← ipa.stack.lambda (fn) `FunctionArn`
- UserPoolArn ← ipa.stack.cognito `UserPoolArn`

**Wirable — Optional** (1) — sourced from upstream stack outputs when streaming Lambda is composed:
- StreamingLambdaFunctionArn ← ipa.stack.lambda (fn-stream) `FunctionArn` (defaults to empty — SSE routes not created)

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| ApiUrl | API Gateway invoke URL (`https://{id}.execute-api.{region}.amazonaws.com/{stage}`) | `{StackName}-ApiUrl` | configure-frontend (API_BASE_URL in config.js), ipa.stack.cloudfront (future) |
| RestApiId | REST API ID | `{StackName}-RestApiId` | Monitoring, reference |
| StageName | Stage name | `{StackName}-StageName` | Reference |

## Security Summary

**Required IAM actions**: apigateway:POST, GET, PUT, DELETE, PATCH on REST API resources + lambda:AddPermission, RemovePermission on Lambda functions — scoped to `{APP_NAMESPACE}-{APP_ENV}-*`
**Security controls**: Cognito authorizer on all non-OPTIONS routes, stage-level throttling (1000/s rate, 500 burst), CORS preflight via MOCK integration (no Lambda invocation)
**Known deferrals**: CORS `Access-Control-Allow-Origin: *` (POC scope), REST API 29s integration timeout (production should use HTTP API v2 for long-polling)
**Full advisory**: See [SECURITY.md](SECURITY.md)
