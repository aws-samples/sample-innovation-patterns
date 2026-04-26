---
title: Overview
sidebar_position: 1
---

# Cognito

The Cognito stack deploys an Amazon Cognito User Pool configured for OAuth 2.0 authentication with OIDC endpoints and a Managed Login UI. It provisions a User Pool with Advanced Security Mode enforced, an app client restricted to the Authorization Code Grant flow, a custom domain prefix with Managed Login v2, and Cognito-provided login branding. The stack serves as the identity provider for all IPA compositions that require authenticated access.

**Template:** `infra/cfn/cognito/cognito.yml`
**Lifecycle:** prepare (one-time)
**Capabilities:** none (no IAM resources)

## Features

- Advanced Security Mode set to ENFORCED for adaptive risk-based authentication and threat protection
- OAuth 2.0 Authorization Code Grant flow with OIDC scopes (`openid`, `profile`, `email`)
- OIDC-compliant endpoints including issuer URL, discovery URL, and end-session endpoint
- Managed Login v2 UI with Cognito-provided branding (no custom CSS or assets required)
- Admin-only user creation — self-registration is disabled
- User enumeration prevention via `PreventUserExistenceErrors`
- Strong password policy requiring uppercase, lowercase, numbers, symbols, and a configurable minimum length
- Auto-verified email attribute for streamlined onboarding
- Token validity set to 8 hours for access and ID tokens, 24 hours for refresh tokens
- Optional deletion protection for production deployments

## When to Use

This stack provides authentication for any IPA composition that serves authenticated users. It is included in the prepare phase when composing any stack that requires authentication and is deployed once per environment before the tier stacks.

The Cognito stack produces the JWT issuer and audience values consumed by downstream stacks:

- **Backend stack** — receives `IssuerUrl` as the `AuthIssuer` parameter and `UserPoolClientId` as the `AuthAudience` parameter for JWT validation on the API Gateway authorizer.
- **Queue stack** — uses the same issuer and audience when queue workers need to validate tokens forwarded from the backend.
- **Frontend stack** — consumes `IssuerUrl` as the OIDC authority, `UserPoolClientId` as the OIDC client ID, `EndSessionEndpoint` for logout, and `HostedUIURL` for login redirection.
