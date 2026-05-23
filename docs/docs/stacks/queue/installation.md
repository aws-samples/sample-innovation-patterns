---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The queue stack is included automatically when selecting the queue stack during `/ipa-compose`. Run the compose skill:

    /ipa-compose

Select the queue stack when prompted for stacks to include. The compose step generates Makefile targets, parameter overrides, and cross-stack wiring for the queue tier.

## Configuration

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `Namespace` | String | Project namespace prefix for resource naming. 1--12 characters, lowercase alphanumeric and hyphens, must start with a letter. |
| `Environment` | String | Deployment environment. Allowed values: `dev`, `staging`, `prod`. |
| `ImageUri` | String | Full ECR image URI including tag (e.g., `123456789012.dkr.ecr.us-east-1.amazonaws.com/repo:latest`). |
| `AuthIssuer` | String | OIDC issuer URL for JWT validation (from Cognito `IssuerUrl` output). |
| `AuthAudience` | String | OIDC client ID for JWT audience validation (from Cognito `UserPoolClientId` output). |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `QueueName` | String | `jobs` | Logical queue name. Physical name: `{Namespace}-{Environment}-{QueueName}`. 1--30 characters, lowercase alphanumeric and hyphens. |
| `VisibilityTimeout` | Number | `300` | Time in seconds a message is hidden after being received. Must exceed the worker Lambda timeout. Range: 0--43200. |
| `MessageRetentionPeriod` | Number | `345600` | Time in seconds messages are retained in the queue (default: 4 days). Range: 60--1209600. |
| `MaxReceiveCount` | Number | `3` | Number of receive attempts before a message is sent to the dead-letter queue. Range: 1--1000. |
| `CreateDLQ` | String | `true` | Whether to create a dead-letter queue for failed messages. Allowed values: `true`, `false`. |
| `FunctionName` | String | `fn-worker` | Worker Lambda function name suffix. 1--24 characters, lowercase alphanumeric and hyphens. |
| `MemorySize` | Number | `512` | Worker Lambda memory allocation in MB. Range: 128--10240. |
| `Timeout` | Number | `300` | Worker Lambda timeout in seconds. Range: 1--900. |
| `ImageCommand` | CommaDelimitedList | `python,-m,sqs_handler` | Worker container CMD override. |
| `EnableJobsTable` | String | `false` | Feature flag: create a DynamoDB jobs table. Allowed values: `true`, `false`. |

## Feature Flags

| Flag | Default | Effect |
|------|---------|--------|
| `EnableJobsTable` | `false` | Creates a DynamoDB table (`{Namespace}_{Environment}_jobs`) with pay-per-request billing and SSE. Adds a conditional IAM policy granting the worker read/write access scoped to the table ARN. |
| `CreateDLQ` | `true` | Creates a dead-letter queue (`{Namespace}-{Environment}-{QueueName}-dlq`) with 14-day retention and SQS-managed encryption. Configures a redrive policy on the main queue with the specified `MaxReceiveCount`. Creates a DLQ depth alarm. |

## Wiring

### Upstream (inputs from prepare stacks)

| Queue Parameter | Source Stack | Source Output | Description |
|-----------------|--------------|---------------|-------------|
| `ImageUri` | ECR | `RepositoryUri` | Container image URI for the worker Lambda. |
| `AuthIssuer` | Cognito | `IssuerUrl` | OIDC issuer URL for JWT validation. |
| `AuthAudience` | Cognito | `UserPoolClientId` | OIDC client ID for JWT audience validation. |

### Downstream (outputs consumed by backend)

| Queue Output | Backend Parameter | Description |
|--------------|-------------------|-------------|
| `QueueUrl` | `SqsQueueUrl` | SQS queue URL passed to the backend Lambda environment. |
| `QueueArn` | `SqsSendQueueArns` | SQS queue ARN used to grant the backend Lambda send permissions. |

The compose step handles all wiring automatically. No manual cross-stack references are required.

## Outputs

| Output | Condition | Description |
|--------|-----------|-------------|
| `QueueUrl` | Always | SQS queue URL. Consumed by the backend stack `SqsQueueUrl` parameter. |
| `QueueArn` | Always | SQS queue ARN. Consumed by the backend stack `SqsSendQueueArns` parameter. |
| `QueueName` | Always | Physical queue name (`{Namespace}-{Environment}-{QueueName}`). |
| `WorkerFunctionArn` | Always | Worker Lambda function ARN. |
| `WorkerFunctionName` | Always | Worker Lambda function name. |
| `DlqUrl` | `CreateDLQ=true` | Dead-letter queue URL. |
| `DlqArn` | `CreateDLQ=true` | Dead-letter queue ARN. |
| `JobsTableArn` | `EnableJobsTable=true` | DynamoDB jobs table ARN. |
