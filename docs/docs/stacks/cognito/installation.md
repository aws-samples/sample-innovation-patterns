---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The Cognito stack is deployed as a prepare-lifecycle stack via `/ipa.compose` when any stack requiring authentication is selected. Run the compose skill:

    /ipa.compose

Select the stacks that require authentication (backend, queue) when prompted. The compose skill automatically includes Cognito as a prepare dependency and generates `scripts/prepare.mk` with all required parameter wiring for the Cognito stack.

To deploy the prepare phase (which includes Cognito):

    /ipa.prepare

The Cognito stack is deployed once per environment. Subsequent deployments of tier stacks reference its outputs through CloudFormation exports.

## Configuration

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `Namespace` | String | Project namespace prefix for resource naming. 1-12 characters, lowercase alphanumeric and hyphens. Default: `app`. |
| `Environment` | String | Deployment environment identifier. 1-12 characters, lowercase letters, digits, and hyphens. Must start with a letter (e.g., `dev`, `staging`, `prod`). |
| `CognitoDomainPrefix` | String | Domain prefix for the Cognito Hosted UI. Must be globally unique across all AWS accounts. Must not contain reserved words: `cognito`, `aws`, `amazon`. |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `CallbackURL` | String | `http://localhost:8080/authentication/callback` | Allowed callback URL for OAuth authentication. The template always includes `http://localhost:8080/authentication/callback` as an additional callback for local development. |
| `MinPasswordLength` | Number | `8` | Minimum password length. Range: 8-99. The password policy always requires uppercase, lowercase, numbers, and symbols regardless of this value. |
| `DeletionProtection` | String | `INACTIVE` | Deletion protection for the User Pool. Set to `ACTIVE` for production environments to prevent accidental deletion. Allowed values: `ACTIVE`, `INACTIVE`. |

### CognitoDomainPrefix Convention

The compose skill generates `CognitoDomainPrefix` using the convention:

    {APP_NAMESPACE}-{APP_ENV}-{APP_ACCOUNT_HASH}

Where `APP_ACCOUNT_HASH` is a short hash derived from the AWS account ID. This convention produces a globally unique prefix without requiring manual coordination. The domain prefix must not contain the words `cognito`, `aws`, or `amazon` -- Cognito rejects these as reserved.

## Outputs

The Cognito stack exports all outputs using the pattern `{StackName}-{OutputKey}`. Downstream stacks reference these exports through the generated Makefile wiring.

| Output | Description | Consumers |
|--------|-------------|-----------|
| `UserPoolId` | Cognito User Pool ID. | Internal reference. Used in OIDC endpoint construction. |
| `UserPoolArn` | Cognito User Pool ARN. | Backend stack (API Gateway Cognito Authorizer configuration). |
| `UserPoolClientId` | App client ID for OAuth 2.0 flows. | Frontend (`OIDC_CLIENT_ID`), Backend (`AUTH_AUDIENCE` Lambda environment variable). |
| `IssuerUrl` | OIDC issuer URL (`https://cognito-idp.{region}.amazonaws.com/{pool-id}`). | Frontend (`OIDC_AUTHORITY`), Backend (`AUTH_ISSUER` Lambda environment variable). |
| `EndSessionEndpoint` | Cognito logout URL (`https://{prefix}.auth.{region}.amazoncognito.com/logout`). | Frontend (`OIDC_END_SESSION_ENDPOINT`). |
| `HostedUIURL` | Full Managed Login URL with pre-configured query parameters for client ID, response type, scopes, and redirect URI. | Frontend (login redirection). |
| `CognitoDomain` | The domain prefix value as registered with Cognito. | Frontend (OIDC authority derivation). |
| `DiscoveryUrl` | OIDC Discovery URL (`https://cognito-idp.{region}.amazonaws.com/{pool-id}/.well-known/openid-configuration`). | Backend (JWT validation libraries for dynamic key fetching). |
