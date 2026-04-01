---
name: ipa-stack-cognito
description: "Deploy a Cognito User Pool stack with OAuth 2.0 Hosted UI and OIDC endpoints."
---

# ipa.stack.cognito

Deploy a Cognito User Pool with App Client, Custom Domain (Hosted UI), and Managed Login Branding. Provides authentication outputs for API Gateway authorizers, Lambda JWT validation, and frontend OIDC flows.

## CloudFormation Contract

- **Template**: `infra/cfn/cognito/cognito.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-cognito`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| CallbackURL | String | `http://localhost:8080/authentication/callback` | `/^https?:\/\/.+$/` | "Must be a valid HTTP(S) URL" |
| CognitoDomainPrefix | String | — | `/^[a-z][a-z0-9-]{0,62}$/` | "Must be 1-63 lowercase chars, starts with letter, no reserved words (cognito, aws, amazon)" |

**CognitoDomainPrefix convention**: Set to `$(APP_NAMESPACE)-$(APP_ENV)-$(APP_ACCOUNT_HASH)` in `--parameter-overrides`. `APP_ACCOUNT_HASH` is a Make variable derived in the Makefile header via `$(shell echo -n "$(AWS_ACCOUNT_ID)" | shasum | cut -c1-8)`. This produces a globally-unique, account-safe domain prefix without exposing the AWS account ID.
| MinPasswordLength | Number | 8 | `8-99` | "Must be between 8 and 99" |
| DeletionProtection | String | INACTIVE | `ACTIVE \| INACTIVE` | "Must be ACTIVE or INACTIVE" |

All parameters are **Configuration** type — sourced from `.env` or defaults. No wirable parameters from other stacks.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| UserPoolId | ID of the Cognito User Pool | `{StackName}-UserPoolId` | Admin operations |
| UserPoolArn | ARN of the Cognito User Pool | `{StackName}-UserPoolArn` | ipa.stack.apigw (CognitoUserPoolArn) |
| UserPoolClientId | ID of the App Client | `{StackName}-UserPoolClientId` | ipa.stack.lambda (AuthAudience) |
| IssuerUrl | OIDC Issuer base URL | `{StackName}-IssuerUrl` | ipa.stack.lambda (AuthIssuer) |
| EndSessionEndpoint | Cognito logout base URL | `{StackName}-EndSessionEndpoint` | Frontend OIDC config |
| HostedUIURL | Full Cognito login URL | `{StackName}-HostedUIURL` | Runbook reference |
| CognitoDomain | Domain prefix value | `{StackName}-CognitoDomain` | Frontend OIDC authority |
| DiscoveryUrl | OIDC Discovery URL | `{StackName}-DiscoveryUrl` | JWT validation libraries |

## Security Summary

**Required IAM actions**: cognito-idp:CreateUserPool, UpdateUserPool, DeleteUserPool, DescribeUserPool, CreateUserPoolClient, UpdateUserPoolClient, DeleteUserPoolClient, CreateUserPoolDomain, DeleteUserPoolDomain, DescribeUserPoolDomain, SetUICustomization, CreateManagedLoginBranding, DeleteManagedLoginBranding — scoped to `arn:aws:cognito-idp:{Region}:{AccountId}:userpool/*`
**Security controls**: Advanced Security Mode ENFORCED, AdminCreateUserOnly, PreventUserExistenceErrors ENABLED, OAuth 2.0 Authorization Code Grant only
**Full advisory**: See [SECURITY.md](SECURITY.md)
