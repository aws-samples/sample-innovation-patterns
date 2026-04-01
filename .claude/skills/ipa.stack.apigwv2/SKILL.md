---
name: ipa-stack-apigwv2
description: "Deploy an HTTP API (API Gateway v2) fronting Lambda with JWT authorizer, buffered and SSE streaming routes."
---

# ipa.stack.apigwv2

Deploy an HTTP API (API Gateway v2) with JWT-based Cognito authorization. Routes buffered traffic (`$default`) to a 30s Lambda integration and streaming traffic (`ANY /api/v1/sse/{proxy+}`) to a 300s Lambda integration. Both integrations point to the same Lambda function. Resolves DEF-002 (REST API 29s integration timeout) by supporting a 5-minute timeout for SSE streaming routes. Provides ApiUrl output for downstream consumers (configure-frontend, CloudFront).

## CloudFormation Contract

- **Template**: `infra/cfn/apigateway-v2/apigateway-v2.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-apigwv2`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| ApiName | String | — | — | — |
| StageName | String | `prod` | — | — |
| LambdaFunctionArn | String | — | — | — |
| IssuerUrl | String | — | — | — |
| UserPoolClientId | String | — | — | — |
| AllowedOrigin | String | `*` | — | — |
| Namespace | String | — | `^[a-z][a-z0-9-]{0,11}$` | Invalid namespace |
| Environment | String | — | `dev`, `staging`, `prod` | — |

### Parameter Classification

**Configuration** (4) — sourced from `.env`, defaults, or auto-generated:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`
- ApiName — passed as `$(APP_NAMESPACE)-$(APP_ENV)-api`
- StageName — hardcoded default `prod`

**Wirable — Required** (3) — sourced from upstream stack outputs:
- LambdaFunctionArn ← ipa.stack.lambda (fn) `FunctionArn`
- IssuerUrl ← ipa.stack.cognito `IssuerUrl`
- UserPoolClientId ← ipa.stack.cognito `UserPoolClientId`

**Wirable — Post-Deploy** (1) — updated after CloudFront deploys:
- AllowedOrigin — defaults to `*`, updated to CloudFront AppUrl via post-deploy step

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| ApiUrl | HTTP API invoke URL (`https://{id}.execute-api.{region}.amazonaws.com/{stage}`) | `{StackName}-ApiUrl` | configure-frontend (API_BASE_URL in config.js), ipa.stack.cloudfront (future) |
| HttpApiId | HTTP API ID | `{StackName}-HttpApiId` | Monitoring, reference |
| StageName | Stage name | `{StackName}-StageName` | Reference |

## Security Summary

**Required IAM actions**: apigateway:POST, GET, PUT, DELETE, PATCH on HTTP API resources (`/apis/*`) + lambda:AddPermission, RemovePermission on Lambda functions — scoped to `{APP_NAMESPACE}-{APP_ENV}-*`
**Security controls**: JWT authorizer on all routes (validates Cognito ID/access tokens), CORS origin scoped to CloudFront domain via post-deploy, Lambda invoke permission scoped to specific HTTP API via SourceArn, CloudWatch access logging (30-day retention)
**Known deferrals**: CORS `*` during initial deploy (auto-wired in post-deploy), no WAF (HTTP API v2 does not support WAF), no mutual TLS (POC scope)
**Full advisory**: See [SECURITY.md](SECURITY.md)
