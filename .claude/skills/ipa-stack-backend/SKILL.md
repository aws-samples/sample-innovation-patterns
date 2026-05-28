---
name: ipa-stack-backend
description: "Deploy a backend tier stack: Lambda + API Gateway v2 + DynamoDB (feature-flagged)."
model: opus
---

# ipa-stack-backend

Deploy a backend tier stack: Lambda + API Gateway v2 + DynamoDB (feature-flagged).

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-backend` |
| Template | `infra/cfn/backend/backend.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | deploy (solution stack) |
| Tier | backend |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Namespace | Yes | — | Project namespace prefix |
| Environment | Yes | — | Deployment environment (dev/staging/prod) |
| ImageUri | Yes | — | ECR image URI with tag |
| AuthIssuer | Yes | — | Cognito OIDC issuer URL |
| AuthAudience | Yes | — | Cognito app client ID |
| FunctionName | No | `fn` | Lambda function name |
| InvokeMode | No | `RESPONSE_STREAM` | Lambda invocation mode |
| MemorySize | No | `512` | Lambda memory in MB |
| Timeout | No | `300` | Lambda timeout in seconds |
| ImageCommand | No | *(empty)* | Override container CMD |
| AllowedOrigin | No | `https://none.invalid` | Allowed CORS origin (CloudFront domain from post-deploy). Blocks cross-origin requests until set. |
| EnablePassengersTable | No | `false` | Feature flag: create passengers DynamoDB table |
| EnableSqsIntegration | No | `false` | Feature flag: enable SQS send permissions |
| SqsQueueUrl | No | *(empty)* | SQS queue URL for env var injection |
| SqsSendQueueArns | No | *(empty)* | SQS queue ARNs for send IAM policy |

## Feature Flags

| Flag | Default | Condition | Controls |
|------|---------|-----------|----------|
| EnablePassengersTable | `false` | HasPassengersTable | PassengersTable resource, DynamoDB IAM policy, PassengersTableArn output |
| EnableSqsIntegration | `false` | HasSqsIntegration | SQS_QUEUE_URL env var, SQS send IAM policy |

## Wirable Parameters

Parameters that receive values from other stacks during composition:

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| ImageUri | ecr | RepositoryUri | Append `:$(IMAGE_TAG)` |
| AuthIssuer | cognito | IssuerUrl | OIDC issuer URL |
| AuthAudience | cognito | UserPoolClientId | App client ID |
| SqsQueueUrl | queue | QueueUrl | Only when EnableSqsIntegration=true. Same-lifecycle wiring (queue → backend, both deploy) — capture at runtime via `$(eval ... describe-stacks ...)` per Case B in MAKEFILE_TEMPLATES.md. Reading from `.env` does NOT work inside a single `make deploy` invocation. |
| SqsSendQueueArns | queue | QueueArn | Only when EnableSqsIntegration=true. Same-lifecycle wiring — see SqsQueueUrl note. |
| AllowedOrigin | frontend | AppUrl | Set during post-deploy (update-backend-cors target) |

## Outputs

| Output | Export Name | Description |
|--------|------------|-------------|
| ApiUrl | `{StackName}-ApiUrl` | HTTP API invoke URL |
| FunctionArn | `{StackName}-FunctionArn` | Lambda function ARN |
| FunctionName | `{StackName}-FunctionName` | Lambda function name |
| PassengersTableArn | `{StackName}-PassengersTableArn` | Conditional (HasPassengersTable) |

## Build Requirements

| Type | Suffix | Dockerfile | Description |
|------|--------|------------|-------------|
| container | rest-lambda | infra/containers/rest-lambda/Dockerfile | Shared container image for backend (REST API handler) and queue (SQS worker). Build context is repo root (`.`). Queue tier reuses this same image and overrides CMD via ImageCommand parameter — do not emit a second `build-rest-lambda` target when queue is in the composition. |

## Security

- Lambda: Per-function execution role with least-privilege policies
- IAM: Conditional DynamoDB policies scoped to `!GetAtt Table.Arn` — no wildcards
- API Gateway: JWT authorizer (Cognito), CORS locked to `AllowedOrigin` parameter (defaults to `https://none.invalid` — blocks cross-origin until post-deploy sets CloudFront domain), access logging
- DynamoDB: SSE enabled, PAY_PER_REQUEST billing
- Log groups: 30-day retention
- ECR pull uses `Resource: '*'` (AWS API limitation — documented)

## CORS Preflight Handling (Terraform-specific)

The Terraform module uses a `$default` catch-all route with `authorization_type = "JWT"`. This route intercepts OPTIONS preflight requests and routes them through the JWT authorizer, which rejects them (preflight has no Bearer token) — causing browser CORS failures.

To prevent this, the TF module includes an explicit `OPTIONS /{proxy+}` route with `authorization_type = "NONE"` that sends preflight requests to the Lambda, where FastAPI's `CORSMiddleware` handles them using `CORS_ALLOWED_ORIGINS`.

The CFN template avoids this by using method-specific routes (`GET /{proxy+}`, `POST /{proxy+}`, etc.) — OPTIONS never matches any route, so API GW's CORS auto-handler responds. When updating either implementation, preserve the corresponding pattern.

## Compose Config

Parameter overrides applied by `/ipa-compose`:

| Parameter | Value | Reason |
|-----------|-------|--------|
| FunctionName | fn | REST API handler |
| InvokeMode | RESPONSE_STREAM | SSE streaming support |
| Timeout | 300 | Long-running inference requests |
| EnablePassengersTable | true | Demo feature — Titanic dataset |

## Deploy Command

```bash
aws cloudformation deploy \
  --template-file infra/cfn/backend/backend.yml \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-backend \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Namespace=$(APP_NAMESPACE) \
    Environment=$(APP_ENV) \
    ImageUri=$(REPO_URI):$(IMAGE_TAG) \
    AuthIssuer=$(AUTH_ISSUER) \
    AuthAudience=$(AUTH_AUDIENCE) \
    EnablePassengersTable=true
```

## Terraform Module

| Property | Value |
|----------|-------|
| Module path | `infra/tf/backend/` |
| State key | `{namespace}-{env}/backend/terraform.tfstate` |
| Required version | `>= 1.5.0` |
| Providers | `hashicorp/aws >= 5.0` |

### Variables

| Variable | Type | Default | Maps to CFN |
|----------|------|---------|-------------|
| namespace | string | — | Namespace |
| environment | string | — | Environment |
| region | string | — | (implicit) |
| state_bucket | string | — | (TF infrastructure) |
| image_uri | string | — | ImageUri |
| auth_issuer | string | — | AuthIssuer |
| auth_audience | string | — | AuthAudience |
| function_name | string | `fn` | FunctionName |
| invoke_mode | string | `RESPONSE_STREAM` | InvokeMode |
| memory_size | number | `512` | MemorySize |
| timeout | number | `300` | Timeout |
| image_command | string | `""` | ImageCommand |
| allowed_origin | string | `https://none.invalid` | AllowedOrigin |
| enable_passengers_table | bool | `false` | EnablePassengersTable |
| enable_sqs_integration | bool | `false` | EnableSqsIntegration |
| sqs_queue_url | string | `""` | SqsQueueUrl |
| sqs_queue_arn | string | `""` | SqsSendQueueArns |

### Outputs

| Output | Maps to CFN |
|--------|-------------|
| api_url | ApiUrl |
| function_arn | FunctionArn |
| function_name | FunctionName |
| passengers_table_arn | PassengersTableArn |

### Remote State References

| Source Module | Data Source | Outputs Used |
|--------------|-------------|--------------|
| cognito | `terraform_remote_state.cognito` | issuer_url, user_pool_client_id |
| ecr | `terraform_remote_state.ecr` | repository_uri |
