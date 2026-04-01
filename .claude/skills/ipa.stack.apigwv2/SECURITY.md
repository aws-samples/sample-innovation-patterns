# Security Advisory: ipa.stack.apigwv2

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the HTTP API (v2) stack.

```yaml
permissions:
  - actions:
      - apigateway:POST
      - apigateway:GET
      - apigateway:PUT
      - apigateway:DELETE
      - apigateway:PATCH
    resource: "arn:aws:apigateway:{AWS_REGION}::/apis/*"
    purpose: "CloudFormation CRUD operations on HTTP API, integrations, routes, authorizers, and stages"

  - actions:
      - lambda:AddPermission
      - lambda:RemovePermission
      - lambda:GetPolicy
    resource: "arn:aws:lambda:{AWS_REGION}:{AWS_ACCOUNT_ID}:function:{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "Grant and revoke API Gateway invoke permission on Lambda function (AWS::Lambda::Permission resource)"

  - actions:
      - logs:CreateLogGroup
      - logs:DeleteLogGroup
      - logs:PutRetentionPolicy
      - logs:DescribeLogGroups
      - logs:TagResource
    resource: "arn:aws:logs:{AWS_REGION}:{AWS_ACCOUNT_ID}:log-group:/aws/apigateway/{APP_NAMESPACE}-{APP_ENV}-apigwv2:*"
    purpose: "CloudFormation CRUD operations on CloudWatch access log group"
```

## Runtime Permissions (Advisory)

No runtime permissions are needed by the HTTP API stack itself. API Gateway is a managed service — AWS handles invocation of Lambda functions using the `AWS::Lambda::Permission` resource-based policy defined in the template.

Consuming services (Lambda functions) need their own permissions for DynamoDB, Bedrock, etc. — those are defined in `ipa.stack.lambda/SECURITY.md`.

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.

```yaml
controls:
  - type: authentication
    enabled: true
    method: "JWT authorizer on all routes — validates Cognito ID tokens and access tokens via IssuerUrl + UserPoolClientId"

  - type: cors
    enabled: true
    method: "Built-in CorsConfiguration on API resource — AllowedOrigin defaults to * during initial deploy, updated to CloudFront domain via post-deploy step"

  - type: access_control
    enabled: true
    method: "Lambda invoke permission scoped to specific HTTP API via SourceArn — prevents cross-API invocation"

  - type: access_logging
    enabled: true
    method: "CloudWatch access logs — 30-day retention, structured JSON format including requestId, routeKey, status, integrationError"

  - type: endpoint_type
    enabled: true
    method: "Regional HTTP API endpoint — no edge-optimized distribution; CloudFront distribution is a separate stack"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No WAF integration | HTTP API v2 does not support WAF | Low — JWT auth provides baseline protection |
| No mutual TLS | POC scope | Low — JWT validation provides authentication |
| CORS `*` during initial deploy | CloudFront domain unknown at API deploy time; updated in post-deploy | Low — window is brief (minutes), JWT auth protects data routes |
