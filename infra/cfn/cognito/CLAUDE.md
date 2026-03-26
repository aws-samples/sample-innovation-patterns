# Cognito User Pool Tool

## Overview

The `cognito-custom-domain.yml` template creates a Cognito User Pool with OAuth/OIDC support and Hosted UI.

## Usage

```python
# TODO: Update usage... 
# deploy_cognito_user_pool(
#     stack_name="my-cognito-stack",
#     user_pool_name="my-user-pool",
#     region="us-east-1",
#     cognito_domain_prefix="myapp-dev-123456789012",
#     callback_url="https://dxxx.cloudfront.net/authentication/callback",
#     namespace="myapp"
# )
```

## Parameters

- `stack_name` (required): CloudFormation stack name
- `user_pool_name` (required): Name of the User Pool
- `region` (required): AWS region
- `profile` (optional): AWS profile name
- `min_password_length` (optional): Minimum password length (default: 8)
- `deletion_protection` (optional): "ACTIVE" or "INACTIVE" (default: "INACTIVE")
- `client_name` (optional): User Pool Client name (basic template only)
- `namespace` (optional): Logical grouping for related stacks
- `cognito_domain_prefix` (optional): Cognito Hosted UI domain prefix — triggers custom domain template
- `callback_url` (optional): OAuth callback URL (default: `http://localhost:8080/authentication/callback`)
- `create_identity_pool` (optional): Create Identity Pool (default: false)

## Output Mapping

| Output | Description | Frontend Consumer | Backend Consumer |
|--------|-------------|-------------------|------------------|
| `UserPoolId` | Cognito User Pool ID | — | — |
| `UserPoolArn` | Cognito User Pool ARN | — | — |
| `UserPoolClientId` | App Client ID | `OIDC_CLIENT_ID` (in `config.js`) | `AUTH_AUDIENCE` (env var) |
| `DiscoveryUrl` | OIDC Discovery URL | — | Agent Core `discovery_url` |
| `IssuerUrl` | OIDC Issuer URL | `OIDC_AUTHORITY` (in `config.js`) | `AUTH_ISSUER` (env var) |
| `CognitoDomain` | Cognito domain prefix | — | — |
| `HostedUIURL` | Login URL | — | — |
| `LogoutURL` | Logout URL | `OIDC_END_SESSION_ENDPOINT` (optional) | — |
| `IdentityPoolId` | Identity Pool ID (conditional) | — | — |

## Security

- Email auto-verification enabled
- Advanced security mode enforced
- `PreventUserExistenceErrors: ENABLED`
- Standard OIDC scopes: `openid`, `profile`, `email`
- No MFA by default
- **Self-registration disabled** — only admins can create users

### Self-Registration Vulnerability

The template sets `AdminCreateUserConfig.AllowAdminCreateUserOnly: true` to disable self-registration. This prevents the "Cognito User Pool Self-Registration Enabled" security finding.

**Do not enable self-registration via Isengard or automated tooling.** If a customer requires self-registration, a human must manually edit the template and set `AllowAdminCreateUserOnly: false` after reviewing the security implications.

## Limitations

- `cognito_domain_prefix` must be globally unique across all AWS accounts
