---
title: /ipa.stack.cognito
sidebar_position: 5
---

# /ipa.stack.cognito

Cognito User Pool with OAuth 2.0 Hosted UI and OIDC endpoints. A prepare-lifecycle stack that persists across deploy/destroy cycles.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-cognito` |
| Template | `infra/cfn/cognito/cognito.yml` |
| Capabilities | None |
| Lifecycle | prepare |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CallbackURL` | `http://localhost:8080/authentication/callback` | OAuth 2.0 callback URL |
| `CognitoDomainPrefix` | `{namespace}-{env}-{account_hash}` | Globally unique Cognito domain prefix |
| `MinPasswordLength` | `8` | Minimum password length |
| `DeletionProtection` | `INACTIVE` | User Pool deletion protection |

## Outputs

| Output | Description |
|--------|-------------|
| `UserPoolId` | Cognito User Pool ID |
| `UserPoolArn` | User Pool ARN |
| `UserPoolClientId` | OIDC audience (client ID) |
| `IssuerUrl` | OIDC issuer URL |
| `EndSessionEndpoint` | Cognito logout URL |
| `HostedUIURL` | Full Cognito login URL |
| `CognitoDomain` | Cognito domain |
| `DiscoveryUrl` | OIDC discovery endpoint |

## Security

- Advanced Security Mode: ENFORCED
- OAuth 2.0 Authorization Code Grant only (no implicit or client credentials)
- HTTPS-only callback URLs in production

## Wiring

Other stacks consume Cognito outputs:

| Consumer | Parameters Wired |
|----------|-----------------|
| Backend | `AuthIssuer` ← `IssuerUrl`, `AuthAudience` ← `UserPoolClientId` |
| Queue | `AuthIssuer` ← `IssuerUrl`, `AuthAudience` ← `UserPoolClientId` |
| CodePipeline | `OidcIssuer`, `OidcClientId`, `OidcEndSessionEndpoint` |

## Related Skills

- [/ipa.prepare](../lifecycle-skills/ipa-prepare.md) — Deploys this stack
- [/ipa.stack.backend](./ipa-stack-backend.md) — Consumes auth issuer and audience
- [/ipa.stack.queue](./ipa-stack-queue.md) — Consumes auth issuer and audience
- [/ipa.stack.codepipeline](./ipa-stack-codepipeline.md) — Consumes OIDC endpoints
