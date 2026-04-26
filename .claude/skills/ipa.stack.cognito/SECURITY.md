# Security Advisory: ipa.stack.cognito

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the Cognito stack.

```yaml
permissions:
  - actions:
      - cognito-idp:CreateUserPool
      - cognito-idp:UpdateUserPool
      - cognito-idp:DeleteUserPool
      - cognito-idp:DescribeUserPool
      - cognito-idp:CreateUserPoolClient
      - cognito-idp:UpdateUserPoolClient
      - cognito-idp:DeleteUserPoolClient
      - cognito-idp:CreateUserPoolDomain
      - cognito-idp:DeleteUserPoolDomain
      - cognito-idp:DescribeUserPoolDomain
      - cognito-idp:SetUICustomization
      - cognito-idp:CreateManagedLoginBranding
      - cognito-idp:DeleteManagedLoginBranding
    resource: "arn:aws:cognito-idp:{AWS_REGION}:{AWS_ACCOUNT_ID}:userpool/*"
    purpose: "CloudFormation CRUD operations on User Pool, App Client, Domain, and Managed Login Branding resources"
```

## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks at runtime. These are **not** consumed by the Builder Execution Role — they are advisory for stacks that integrate with Cognito (e.g., Lambda functions performing JWT validation).

```yaml
runtime_permissions:
  - actions:
      - cognito-idp:DescribeUserPool
      - cognito-idp:DescribeUserPoolClient
    resource: "!Output UserPoolArn"
    purpose: "Runtime JWT token validation and JWKS key retrieval by consuming Lambda functions"
```

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.

```yaml
controls:
  - type: advanced_security
    enabled: true
    method: "AdvancedSecurityMode ENFORCED — adaptive authentication, compromised credential protection, risk-based adaptive challenges"

  - type: user_creation
    enabled: true
    method: "AdminCreateUserConfig.AllowAdminCreateUserOnly: true — no self-registration; users created by administrators only"

  - type: token_security
    enabled: true
    method: "PreventUserExistenceErrors ENABLED — prevents user enumeration via authentication API error messages"

  - type: authentication
    enabled: true
    method: "OAuth 2.0 Authorization Code Grant only (AllowedOAuthFlows: code) — no implicit grant; PKCE supported via client-side flows"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| MFA not enabled by default | POC scope — configurable via future parameter | Medium — mitigated by Advanced Security Mode adaptive authentication |
| Password policy uses MinPasswordLength only | POC simplification — template enforces lowercase, uppercase, numbers, symbols | Low — complexity requirements are enforced, only minimum length is configurable |
| No Identity Pool provisioned | Not needed for JWT-based API Gateway + Lambda auth | Low — separate stack skill if direct AWS service access needed |
| Token validity: 8h access/ID, 24h refresh | POC defaults — not parameterized | Low — acceptable for development; customer can modify template |
