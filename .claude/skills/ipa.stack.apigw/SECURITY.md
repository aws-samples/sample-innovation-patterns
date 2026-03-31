# Security Advisory: ipa.stack.apigw

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the API Gateway stack.

```yaml
permissions:
  - actions:
      - apigateway:POST
      - apigateway:GET
      - apigateway:PUT
      - apigateway:DELETE
      - apigateway:PATCH
    resource: "arn:aws:apigateway:{AWS_REGION}::/restapis/*"
    purpose: "CloudFormation CRUD operations on REST API, resources, methods, authorizers, deployments, and stages"

  - actions:
      - lambda:AddPermission
      - lambda:RemovePermission
      - lambda:GetPolicy
    resource: "arn:aws:lambda:{AWS_REGION}:{AWS_ACCOUNT_ID}:function:{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "Grant and revoke API Gateway invoke permission on buffered and streaming Lambda functions (AWS::Lambda::Permission resources)"
```

## Runtime Permissions (Advisory)

No runtime permissions are needed by the API Gateway stack itself. API Gateway is a managed service — AWS handles invocation of Lambda functions using the `AWS::Lambda::Permission` resource-based policies defined in the template.

Consuming services (Lambda functions) need their own permissions for DynamoDB, Bedrock, etc. — those are defined in `ipa.stack.lambda/SECURITY.md`.

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.

```yaml
controls:
  - type: authentication
    enabled: true
    method: "COGNITO_USER_POOLS authorizer on all non-OPTIONS methods — validates Cognito ID tokens from Authorization header"

  - type: throttling
    enabled: true
    method: "Stage-level rate limiting — 1000 requests/second steady-state, 500 burst limit — applied to all methods via MethodSettings"

  - type: cors_preflight
    enabled: true
    method: "OPTIONS methods use MOCK integration — CORS preflight requests are handled without invoking Lambda, reducing cost and latency"

  - type: access_control
    enabled: true
    method: "Lambda invoke permissions scoped to specific REST API via SourceArn — prevents cross-API invocation"

  - type: endpoint_type
    enabled: true
    method: "REGIONAL endpoint — no edge-optimized distribution; CloudFront distribution is a separate stack when needed"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| CORS Access-Control-Allow-Origin: * | POC scope — at API Gateway deploy time, CloudFront domain is unknown (deploys later). Production should scope to specific domain. | Low — mitigated by Cognito authorization on all data routes; only preflight responses are affected |
| REST API 29s integration timeout | REST API Gateway hard limit. Streaming Lambda returns chunked responses within this window. | Medium — production SSE use cases should migrate to HTTP API (v2) which supports 5-minute timeouts |
| No access logging to CloudWatch | LogGroup removed per POC scope decision (Q3:C). Account-level API Gateway logging role not configured. | Low — Lambda-level CloudWatch Logs still capture all request processing; API Gateway access logs are a production concern |
| No WAF integration | POC scope — Web Application Firewall is not configured | Low — Cognito authorization and throttling provide baseline protection |
| No mutual TLS | POC scope — client certificate authentication not configured | Low — Cognito ID token validation provides authentication |
