---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The backend stack is included automatically when composing the `react-rest-lambda` pattern. Run the compose skill and select the pattern:

    /ipa.compose

Select `react-rest-lambda` when prompted. The compose skill generates the deployment Makefile with all required parameter wiring.

## Configuration

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `Namespace` | String | Project namespace prefix for resource naming. 1-12 characters, lowercase alphanumeric and hyphens, must start with a letter. |
| `Environment` | String | Deployment environment. Allowed values: `dev`, `staging`, `prod`. |
| `ImageUri` | String | Full ECR image URI including tag (e.g., `123456789012.dkr.ecr.us-east-1.amazonaws.com/repo:latest`). |
| `AuthIssuer` | String | OIDC issuer URL for JWT validation. Sourced from the Cognito stack `IssuerUrl` output. |
| `AuthAudience` | String | OIDC client ID for JWT audience validation. Sourced from the Cognito stack `UserPoolClientId` output. |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `FunctionName` | String | `fn` | Logical function name for the backend Lambda. 1-24 characters, lowercase alphanumeric and hyphens. |
| `InvokeMode` | String | `RESPONSE_STREAM` | Lambda invocation mode. Allowed values: `BUFFERED`, `RESPONSE_STREAM`. |
| `MemorySize` | Number | `512` | Lambda memory allocation in MB. Range: 128-10240. |
| `Timeout` | Number | `300` | Lambda timeout in seconds. Range: 1-900. |
| `ImageCommand` | CommaDelimitedList | *(empty)* | Override container CMD (e.g., `python,-m,handler`). Leave empty to use the Dockerfile CMD. |
| `AlarmSnsTopicArn` | String | *(empty)* | SNS topic ARN for alarm actions. Leave empty to keep alarms in a disabled state. |

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `EnablePassengersTable` | `false` | Creates a DynamoDB table (`{Namespace}_{Environment}_passengers`) for passenger data. Adds a conditional least-privilege IAM policy to the Lambda execution role granting read/write access to the table. |
| `EnableSqsIntegration` | `false` | Adds SQS `SendMessage` and `GetQueueAttributes` permissions to the Lambda execution role and injects the `SQS_QUEUE_URL` environment variable into the function. Also grants access to the convention-based jobs table (`{Namespace}_{Environment}_jobs`). Enabled automatically when composed with the `sqs-lambda` pattern. |

When `EnableSqsIntegration` is set to `true`, the following additional parameters become relevant:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SqsQueueUrl` | String | *(empty)* | SQS queue URL injected as the `SQS_QUEUE_URL` environment variable. |
| `SqsSendQueueArns` | String | *(empty)* | Comma-separated SQS queue ARNs for send permissions. |

## Wiring

The backend stack receives values from upstream stacks. The compose skill wires these automatically in the generated Makefile.

| Backend Parameter | Source Stack | Source Output | Notes |
|-------------------|-------------|---------------|-------|
| `ImageUri` | ECR | `RepositoryUri` | Append image tag (e.g., `:latest`) |
| `AuthIssuer` | Cognito | `IssuerUrl` | OIDC issuer endpoint |
| `AuthAudience` | Cognito | `UserPoolClientId` | OIDC client ID |
| `SqsQueueUrl` | Queue | `QueueUrl` | Only when `EnableSqsIntegration=true` |
| `SqsSendQueueArns` | Queue | `QueueArn` | Only when `EnableSqsIntegration=true` |

## Outputs

| Output | Description | Export Name |
|--------|-------------|-------------|
| `ApiUrl` | HTTP API invoke URL (application entry point). Format: `https://{api-id}.execute-api.{region}.amazonaws.com/prod` | `{StackName}-ApiUrl` |
| `FunctionArn` | Lambda function ARN | `{StackName}-FunctionArn` |
| `FunctionName` | Lambda function name | `{StackName}-FunctionName` |
| `DashboardUrl` | Direct URL to the CloudWatch backend dashboard | `{StackName}-DashboardUrl` |
| `PassengersTableArn` | DynamoDB passengers table ARN. **Conditional** -- only present when `EnablePassengersTable=true`. | `{StackName}-PassengersTableArn` |
