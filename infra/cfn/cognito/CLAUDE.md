# Cognito User Pool Stack

## Overview

The `cognito.yml` template creates a Cognito User Pool with OAuth 2.0 Hosted UI, OIDC endpoints, and Managed Login Branding. This is the IPA stack skill template for `ipa.stack.cognito`.

**Stack name convention**: `{APP_NAMESPACE}-{APP_ENV}-cognito`

## Deployment

```bash
uv run deploy cfn \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-cognito \
  --template infra/cfn/cognito/cognito.yml \
  --parameter-overrides \
    Namespace=$(APP_NAMESPACE) \
    Environment=$(APP_ENV) \
    CallbackURL=http://localhost:8080/authentication/callback \
    CognitoDomainPrefix=$(APP_NAMESPACE)-$(APP_ENV)-$(AWS_ACCOUNT_ID)
```

No `--capabilities` flag needed — this template does not create IAM roles.

## Parameters

| Parameter | Type | Default | Required | Notes |
|-----------|------|---------|----------|-------|
| `Namespace` | String | `app` | Yes | 1-12 lowercase alphanumeric + hyphens |
| `Environment` | String | — | Yes | `dev`, `staging`, or `prod` |
| `MinPasswordLength` | Number | `8` | No | Range: 8–99 |
| `DeletionProtection` | String | `INACTIVE` | No | `ACTIVE` or `INACTIVE` |
| `CallbackURL` | String | `http://localhost:8080/authentication/callback` | No | OAuth callback URL |
| `CognitoDomainPrefix` | String | — | Yes | Globally unique; must not contain `cognito`, `aws`, `amazon` |

## Output Mapping

| Output | Description | Frontend Consumer | Backend Consumer |
|--------|-------------|-------------------|------------------|
| `UserPoolId` | Cognito User Pool ID | — | — |
| `UserPoolArn` | Cognito User Pool ARN | — | API Gateway (Cognito Authorizer) |
| `UserPoolClientId` | App Client ID | `OIDC_CLIENT_ID` | `AUTH_AUDIENCE` (Lambda env var) |
| `IssuerUrl` | OIDC Issuer URL | `OIDC_AUTHORITY` | `AUTH_ISSUER` (Lambda env var) |
| `EndSessionEndpoint` | Cognito logout base URL | `OIDC_END_SESSION_ENDPOINT` | — |
| `HostedUIURL` | Full login URL | — | — |
| `CognitoDomain` | Domain prefix value | OIDC authority derivation | — |
| `DiscoveryUrl` | OIDC Discovery URL | — | JWT validation libraries |

## Resources (4)

- `CognitoUserPool` — User Pool with advanced security, admin-only creation
- `CognitoUserPoolClient` — App Client with OAuth 2.0 authorization code grant
- `CognitoUserPoolDomain` — Custom domain prefix with Managed Login v2
- `ManagedLoginBranding` — Managed Login UI branding (depends on domain)

## Security

- Advanced Security Mode: **ENFORCED**
- Self-registration: **Disabled** (AdminCreateUserOnly)
- User enumeration prevention: **ENABLED** (PreventUserExistenceErrors)
- OAuth flow: **Authorization Code Grant only** (no implicit grant)
- OIDC scopes: `openid`, `profile`, `email`
- No MFA by default (POC scope — mitigated by Advanced Security Mode)
- No IAM roles in this template (Identity Pool removed from base stack)

## Limitations

- `CognitoDomainPrefix` must be globally unique across all AWS accounts
- Must not contain reserved words: `cognito`, `aws`, `amazon`
- Managed Login Branding (`AWS::Cognito::ManagedLoginBranding`) requires AWS commercial regions
- Token validity is hardcoded: 8h access/ID tokens, 24h refresh tokens
- Identity Pool is not included — use a separate stack if direct AWS service access is needed from the frontend
