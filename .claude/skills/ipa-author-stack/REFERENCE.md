# Stack Authoring Reference

Structural contracts, templates, and conventions for IPA stack skills.
Load this file at the start of authoring — all sections are needed
throughout the workflow.

**Sections 1-9: Stack Skill Authoring**
Define how to create SKILL.md, SECURITY.md, TROUBLESHOOT.md, and
CloudFormation templates for individual stack skills.

---

## 1. SKILL.md Structure

Every stack skill SKILL.md follows this exact section order. All sections are mandatory unless marked optional.

### Frontmatter

~~~yaml
---
name: ipa-stack-{service}
description: "{One sentence: Deploy a [resource] for [purpose].}"
---
~~~

- `name` is kebab-case, prefixed with `ipa-stack-`.
- `description` is a single sentence. No trigger phrases — stack skills are invoked by `ipa-compose`, not directly by users.

### H1 Title and Summary Paragraph

~~~markdown
# ipa.stack.{service}

{One paragraph: what this stack deploys, what outputs it provides, and what downstream
consumers use it. Mention multi-instance support if applicable.}
~~~

### CloudFormation Contract

Three bullet points, always in this order:

~~~markdown
## CloudFormation Contract

- **Template**: `infra/cfn/{service}/{service}.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-{suffix}`
- **Capabilities**: none
~~~

- Template path is always `infra/cfn/{service}/{service}.yml`.
- Stack name suffix defaults to the service name. Multi-instance stacks note the variable suffix (e.g., `ddb-{model}`).
- Capabilities is `none` unless the template creates IAM resources, in which case `CAPABILITY_NAMED_IAM`.

### Parameters Table

~~~markdown
## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| {ServiceParam} | {Type} | {default or —} | {pattern or allowed values} | "{error message}" |
~~~

- Namespace and Environment rows are always first, with the exact validation patterns shown above.
- Default column: use `—` for required parameters with no default, the default value for optional parameters, `(empty)` for wirable-optional parameters that default to empty string.
- Validation column: use regex patterns in `/pattern/` format or pipe-separated allowed values.

### Parameter Classification

Immediately follows the Parameters table as a subsection:

~~~markdown
### Parameter Classification

**Configuration** ({count}) — sourced from `.env` or defaults:
- Namespace — from `APP_NAMESPACE` in `.env`
- Environment — from `APP_ENV` in `.env`
- {ParamName} — {source description}

**Wirable — Required** ({count}) — sourced from upstream stack outputs:
- {ParamName} <- ipa.stack.{source} `{OutputKey}`

**Wirable — Optional** ({count}) — sourced from upstream stack outputs when composed:
- {ParamName} <- ipa.stack.{source} `{OutputKey}` (defaults to empty — {behavior when empty})
~~~

- Omit any classification category that has zero parameters (except Configuration, which always has at least Namespace and Environment).
- The `<-` arrow format is parsed by `ipa-compose` for auto-wiring. Use it exactly.
- For Pattern-provided parameters, add a fourth category:

~~~markdown
**Pattern-provided** ({count}) — sourced from `.env` via convention:
- {ParamName} — from `{ENV_VAR_CONVENTION}` in `.env`
~~~

### Outputs Table

~~~markdown
## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| {OutputKey} | {description} | `{StackName}-{OutputKey}` | {consumer description} |
~~~

- Export Convention is always `{StackName}-{OutputKey}`.
- Used By column format:
  - For wired parameters: `ipa.stack.{consumer} ({ParameterName})`
  - For operational consumers: `{step description}` (e.g., `post-deploy.mk upload-frontend`)
  - For multiple consumers: comma-separated

### Build Requirements (Optional)

Include only if the stack requires a pre-built artifact (container image, frontend bundle):

~~~markdown
## Build Requirements

This stack requires a {artifact type} before deployment.

| Type | Suffix | Dockerfile | Description |
|------|--------|------------|-------------|
| container | {suffix} | {path/to/Dockerfile} | {description} |
~~~

### Naming Convention (Optional)

Include only if physical resource naming differs from stack naming:

~~~markdown
## Naming Convention

Physical {resource} names follow: `{pattern}`

Examples:
- Namespace=`app`, Environment=`dev`, {Param}=`value` -> `app_dev_value`
~~~

### Security Summary

~~~markdown
## Security Summary

**Required IAM actions**: {comma-separated actions} — scoped to `{resource ARN pattern}`
**Runtime permissions**: {description, or omit line if none}
**Security controls**: {comma-separated controls}
**Known deferrals**: See [SECURITY.md](SECURITY.md)
**Full advisory**: See [SECURITY.md](SECURITY.md)
~~~

---

## 2. SECURITY.md Structure

### Header

~~~markdown
# Security Advisory: ipa.stack.{service}
~~~

### Deployment Permissions

IAM actions the Builder Execution Role needs. One YAML block per resource scope:

~~~markdown
## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the {service} stack.
~~~

Then a yaml code block:

~~~yaml
permissions:
  - actions:
      - {service}:{Action1}
      - {service}:{Action2}
    resource: "arn:aws:{service}:{AWS_REGION}:{AWS_ACCOUNT_ID}:{resource-type}/{APP_NAMESPACE}-{APP_ENV}-{suffix}"
    purpose: "CloudFormation CRUD operations on {resource description}"
~~~

- Scope to the tightest resource ARN possible.
- Use `*` only when AWS does not support resource-level permissions for that action — document this in the `purpose` field.
- Group actions by resource scope. If the template creates resources across multiple services (e.g., Lambda + IAM + Logs), create a separate `- actions:` block for each.

### Runtime Permissions (Optional)

Include only if the deployed resource grants runtime permissions to other services:

~~~markdown
## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks at runtime. These are **not** consumed by the Builder Execution Role — they are advisory for stacks that integrate with {service}.
~~~

Then a yaml code block:

~~~yaml
runtime_permissions:
  - actions:
      - {service}:{RuntimeAction}
    resource: "{output reference or ARN pattern}"
    purpose: "{runtime use case}"
~~~

### Security Controls

~~~markdown
## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.
~~~

Then a yaml code block:

~~~yaml
controls:
  - type: {control_type}
    enabled: true
    method: "{description of the control}"
~~~

Valid control types:
- `encryption` — at-rest and in-transit encryption
- `access_control` — public access blocks, IAM-only access
- `logging` — log retention, audit trails
- `iam` — least-privilege roles, no shared roles
- `deletion_safety` — deletion protection, non-empty checks
- `conditional_permissions` — permissions only created when needed

### Known Deferrals

~~~markdown
## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| {what is deferred} | {why — typically POC scope} | {Low/Medium/High — with brief justification} |
~~~

- Every deferral must have all three columns populated.
- Risk levels: Low (no immediate impact, easy to add later), Medium (should be addressed before staging), High (must be addressed before production).

---

## 3. TROUBLESHOOT.md Structure

### Header and Failure Catalog

~~~markdown
# Troubleshooting: ipa.stack.{service}

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails | `deploy-{suffix}` fails with CREATE_FAILED or parameter validation error | {typical causes} | {recovery steps with exact commands} |
| 2 | Stack deletion fails | `aws cloudformation delete-stack` fails or hangs | {typical causes} | {recovery steps with exact commands} |
| 3 | No updates to be performed | `aws cloudformation deploy` reports no changes | Parameters and template unchanged since last deployment | Not an error — stack is already in desired state. `--no-fail-on-empty-changeset` flag handles this. |
~~~

Minimum three rows: creation failure, deletion failure, no-updates. Add service-specific failure modes as additional rows.

### Additional Troubleshooting

Service-specific issues as H3 subsections:

~~~markdown
## Additional Troubleshooting

### {Issue title}

**Symptom**: {what the user sees}

**Root Cause**: {why it happens}

**Recovery**: {exact steps to fix, with commands}
~~~

---

## 4. CloudFormation Template Skeleton

~~~yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: '{Short description of what this template deploys}'

Parameters:
  Namespace:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter'
    Description: 'Namespace prefix for resource names (1-12 lowercase alphanumeric + hyphens)'

  Environment:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter'
    Description: 'Deployment environment'

  # Service-specific parameters below.
  # For AllowedValues, use:
  #   AllowedValues: ['value1', 'value2']
  # For AllowedPattern, use:
  #   AllowedPattern: '^pattern$'
  #   ConstraintDescription: 'Human-readable error message'

# Optional: Conditions for optional wirable parameters
# Conditions:
#   HasOptionalParam: !Not [!Equals [!Ref OptionalParam, '']]

Resources:
  # Resource naming convention:
  #   !Sub '${Namespace}-${Environment}-{resource-suffix}'
  #
  # Tag every taggable resource:
  #   Tags:
  #     - Key: Environment
  #       Value: !Ref Environment
  #
  # Use !Sub for all dynamic values — never hardcode account IDs or regions.
  # Use !GetAtt and !Ref for cross-resource references within the template.
  # Use Conditions to conditionally create resources based on optional parameters.

Outputs:
  # Every output MUST be exported:
  #
  # {OutputKey}:
  #   Description: '{description}'
  #   Value: {!GetAtt Resource.Attribute or !Ref Resource}
  #   Export:
  #     Name: !Sub '${AWS::StackName}-{OutputKey}'
  #
  # OutputKey naming: PascalCase, descriptive, matches what downstream consumers expect.
  # The Export Name convention is mandatory for ipa-compose wiring compatibility.
~~~

### Key CFN Conventions

- **Namespace and Environment** are always the first two parameters with the exact AllowedPattern shown above.
- **Resource naming** uses `!Sub '${Namespace}-${Environment}-{suffix}'` — never hardcoded values.
- **No hardcoded account IDs or regions** — use `${AWS::AccountId}` and `${AWS::Region}` pseudo-parameters.
- **All outputs are exported** via `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.
- **Conditions** gate optional resources: `HasX: !Not [!Equals [!Ref X, '']]` with `Condition: HasX` on the resource.
- **ConstraintDescription** on every parameter with AllowedPattern — this is the error message the user sees on validation failure.
- **Description** on every parameter — CloudFormation displays these in the console.

---

## 5. Parameter Classification Rules

Parameters fall into four categories. The classification determines how `ipa-compose` wires values in generated Makefiles.

### Configuration

Sourced from `.env` variables or template defaults. Passed directly as `--parameter-overrides` in the Makefile deploy target.

**Always present:**
- `Namespace` — from `APP_NAMESPACE`
- `Environment` — from `APP_ENV`

**Existing examples across stacks:**

| Parameter | Stack | Default | Source |
|-----------|-------|---------|--------|
| MemorySize | lambda | 512 | Template default |
| Timeout | lambda | 30 | Template default |
| BillingMode | dynamodb | PAY_PER_REQUEST | Template default |
| MinPasswordLength | cognito | 8 | Template default |
| BucketNameSuffix | s3 | web | Template default |
| DeletionProtection | cognito | INACTIVE | Template default |
| CallbackURL | cognito | http://localhost:8080/... | Template default, overridden in prepare.mk |
| CognitoDomainPrefix | cognito | — | Derived in Makefile from APP_NAMESPACE + APP_ENV + account hash |

### Wirable -- Required

Must be populated from an upstream stack's output. `ipa-compose` generates `$(eval)` lines in the Makefile to fetch these at deploy time:

~~~makefile
$(eval IMAGE_URI := $(shell aws cloudformation describe-stacks \
    --stack-name $(APP_NAMESPACE)-$(APP_ENV)-ecr \
    --query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
    --output text \
    $(if $(AWS_PROFILE),--profile $(AWS_PROFILE),) $(if $(AWS_REGION),--region $(AWS_REGION),)))
~~~

**Naming rule**: The parameter name should match or closely correspond to the upstream output name for auto-wiring. Exact name matches are auto-wired by `ipa-compose`; mismatches require explicit wiring.

**Existing examples:**

| Parameter | Stack | Source Stack | Source Output |
|-----------|-------|-------------|---------------|
| ImageUri | lambda | ecr | RepositoryUri |
| AuthIssuer | lambda | cognito | IssuerUrl |
| AuthAudience | lambda | cognito | UserPoolClientId |
| LogBucketName | s3 | ipa-security | LogBucketName |
| CognitoUserPoolArn | apigw | cognito | UserPoolArn |
| LambdaFunctionArn | apigw/apigwv2 | lambda | FunctionArn |
| BucketArn | cloudfront | s3 | BucketArn |
| BucketDomainName | cloudfront | s3 | BucketDomainName |

### Wirable -- Optional

Defaults to empty string. The CFN template uses a Condition to enable/disable resources or permissions based on whether the parameter is non-empty.

**Template pattern:**

~~~yaml
Parameters:
  OptionalParam:
    Type: String
    Default: ''

Conditions:
  HasOptionalParam: !Not [!Equals [!Ref OptionalParam, '']]

Resources:
  ConditionalResource:
    Type: ...
    Condition: HasOptionalParam
~~~

**Existing examples:**

| Parameter | Stack | Source Stack | Source Output | Behavior When Empty |
|-----------|-------|-------------|---------------|-------------------|
| DynamoDbTableArns | lambda | dynamodb | TableArn | No DynamoDB IAM policy created |
| StreamingLambdaFunctionArn | apigwv2 | lambda | FunctionArn | No SSE streaming routes created |
| LogBucketName | lambda | ipa-security | LogBucketName | No S3 access log delivery |

### Pattern-provided

Sourced from `.env` via a naming convention. Used for multi-instance stacks where each instance gets a different value.

**Existing examples:**

| Parameter | Stack | Convention | Example |
|-----------|-------|-----------|---------|
| TableName | dynamodb | `APP_DDB_TABLE_{MODEL}` | `APP_DDB_TABLE_PASSENGERS=passengers` |
| FunctionName | lambda | Set per-instance in compose config | `fn`, `fn-stream` |

---

## 6. Output Export Convention

Every output must use the export pattern:

~~~yaml
{OutputKey}:
  Description: '{description}'
  Value: {!GetAtt or !Ref}
  Export:
    Name: !Sub '${AWS::StackName}-{OutputKey}'
~~~

This produces exports like `myapp-dev-cognito-UserPoolId` which `ipa-compose` fetches via:

~~~makefile
$(eval USER_POOL_ID := $(shell aws cloudformation describe-stacks \
    --stack-name $(APP_NAMESPACE)-$(APP_ENV)-cognito \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text \
    $(if $(AWS_PROFILE),--profile $(AWS_PROFILE),) $(if $(AWS_REGION),--region $(AWS_REGION),)))
~~~

**Used By tracking**: Every output's "Used By" column in the SKILL.md Outputs table must list all downstream consumers. Format:
- `ipa.stack.{consumer} ({ParameterName})` — for wired parameters
- `{operational step}` — for non-stack consumers (e.g., `post-deploy.mk upload-frontend`)

---

## 7. Naming Conventions

### Stack Names

~~~text
{APP_NAMESPACE}-{APP_ENV}-{suffix}
~~~

- Hyphens only, no underscores.
- Suffix defaults to the service name (e.g., `ecr`, `cognito`, `s3`, `apigwv2`).
- Multi-instance stacks use extended suffixes (e.g., `ddb-passengers`, `fn-stream`).

### Physical Resource Names

Most resources use the stack naming convention (hyphens). Known exceptions:
- **DynamoDB tables**: `{Namespace}_{Environment}_{TableName}` (underscores) — convention-based runtime lookup via `PynamodbUtil.env_table_name()`.
- **ECR repositories**: `{Namespace}-{Environment}-ecr` (hyphens, matches stack name).

When creating a new stack skill, determine whether the AWS service has naming constraints that require a different convention. Document any deviation in the Naming Convention section of SKILL.md.

### Directory Names

- Skill directory: `.claude/skills/ipa.stack.{service}/`
- CFN template directory: `infra/cfn/{service}/`
- Service name should be short and lowercase (e.g., `sqs`, `sns`, `rds`, `efs`).

---

## 8. Wiring Compatibility

For `ipa-compose` to consume a stack skill, the SKILL.md must contain these sections with these exact heading names:

| Required Section | Heading | Purpose |
|-----------------|---------|---------|
| CloudFormation Contract | `## CloudFormation Contract` | Template path, stack name, capabilities |
| Parameters | `## Parameters` | Parameter table with validation |
| Parameter Classification | `### Parameter Classification` | Classification under Parameters section |
| Outputs | `## Outputs` | Output table with export convention and Used By |

The compose skill's validation procedure (V3) checks for these sections and fails if any are missing.

### How Compose Reads Stack Skills

1. **Template path** — parsed from the `Template:` bullet in CloudFormation Contract.
2. **Stack name suffix** — parsed from the `Stack name:` bullet, extracting the `{suffix}` after `{APP_NAMESPACE}-{APP_ENV}-`.
3. **Capabilities** — parsed from the `Capabilities:` bullet.
4. **Parameters** — parsed from the Parameters table. Column headers must be: Parameter, Type, Default, Validation, Error Message.
5. **Parameter Classification** — parsed for wiring. The `<-` arrow notation (`{ParamName} <- ipa.stack.{source} \`{OutputKey}\``) tells compose which upstream output provides each wirable parameter.
6. **Outputs** — parsed from the Outputs table. Column headers must be: Output, Description, Export Convention, Used By.

### Auto-Wiring Resolution

When `ipa-compose` resolves wiring (Step 0.7):
1. For each Wirable parameter, it searches all composed stacks' Outputs for a name match.
2. **Exact match** (output name == parameter name) -> auto-wired.
3. **Multiple matches** -> builder selects.
4. **No match** -> marked unresolved (manual Makefile edit required).

To maximize auto-wiring success: name wirable parameters to match their upstream output names when possible. When names must differ (e.g., `AuthIssuer` <- `IssuerUrl`), `ipa-compose` requires explicit wiring configuration.

---

## 9. Existing Stack Inventory

Reference for understanding the current ecosystem and avoiding naming or suffix collisions.

| Stack | Suffix | Capabilities | Lifecycle | Notes |
|-------|--------|-------------|-----------|-------|
| ipa-stack-cognito | cognito | none | prepare | Authentication provider |
| ipa-stack-ecr | ecr | none | prepare | Container registry |
| ipa-stack-frontend | frontend | none | deploy | Consolidated: S3 + CloudFront + OAC |
| ipa-stack-backend | backend | CAPABILITY_NAMED_IAM | deploy | Consolidated: Lambda + API GW v2 + DynamoDB + CloudWatch |
| ipa-stack-queue | queue | CAPABILITY_NAMED_IAM | deploy | Consolidated: SQS + DLQ + worker Lambda + ESM + DynamoDB + CloudWatch |

---

## 10. Available Stack Inventory

Existing stack skills. Use this to understand the current ecosystem, avoid naming collisions, and plan wiring for new stacks.

**Stack types:**
- **Tier stacks** — Consolidated stacks that bundle related AWS services into a single deployable unit with feature flags for optional resources. Tier stacks internalize many cross-service wiring connections (e.g., Lambda↔API Gateway, Lambda↔DynamoDB, Lambda↔CloudWatch are all handled within the tier template), resulting in simpler inter-stack wiring.
- **Prepare stacks** — One-time prerequisite resources that survive teardown.

### Tier Stacks

#### ipa-stack-backend (Lifecycle: deploy)

**Suffix**: `backend` | **Capabilities**: CAPABILITY_NAMED_IAM | **Tier**: backend

Consolidated backend tier: Lambda + API Gateway v2 (JWT authorizer, CORS, SSE streaming) + DynamoDB (feature-flagged) + CloudWatch dashboard.

**Parameters** (beyond Namespace/Environment):

| Parameter | Classification | Default | Description |
|-----------|---------------|---------|-------------|
| ImageUri | Wirable — Required | — | ECR image URI with tag |
| AuthIssuer | Wirable — Required | — | Cognito OIDC issuer URL |
| AuthAudience | Wirable — Required | — | Cognito app client ID |
| FunctionName | Config | `fn` | Lambda function name |
| InvokeMode | Config | `RESPONSE_STREAM` | Lambda invocation mode |
| MemorySize | Config | `512` | Lambda memory (MB) |
| Timeout | Config | `300` | Lambda timeout (seconds) |
| ImageCommand | Config | *(empty)* | Override container CMD |
| EnablePassengersTable | Feature Flag | `false` | Create passengers DynamoDB table |
| EnableSqsIntegration | Feature Flag | `false` | Enable SQS send permissions + env var |
| SqsQueueUrl | Wirable — Optional | *(empty)* | SQS queue URL (when EnableSqsIntegration=true) |
| SqsSendQueueArns | Wirable — Optional | *(empty)* | SQS queue ARNs for send policy (when EnableSqsIntegration=true) |
| AlarmSnsTopicArn | Wirable — Optional | *(empty)* | SNS topic for alarm actions |

**Feature Flags:**

| Flag | Default | Controls |
|------|---------|----------|
| EnablePassengersTable | `false` | PassengersTable resource, DynamoDB IAM policy, PassengersTableArn output |
| EnableSqsIntegration | `false` | SQS_QUEUE_URL env var, SQS send IAM policy |

**Outputs**:

| Output | Typical Consumers |
|--------|------------------|
| ApiUrl | Post-deploy (configure-frontend, update-backend-cors) |
| FunctionArn | Monitoring |
| FunctionName | Monitoring, invoke commands |
| DashboardUrl | Observability |
| PassengersTableArn | Conditional (HasPassengersTable) |

**Internal composition** (no external wiring needed): Lambda↔API Gateway v2, Lambda↔DynamoDB, Lambda↔CloudWatch — all connected via `!GetAtt` and `!Ref` within the template.

---

#### ipa-stack-frontend (Lifecycle: deploy)

**Suffix**: `frontend` | **Capabilities**: none | **Tier**: frontend

Consolidated frontend tier: S3 static hosting + CloudFront distribution + OAC.

**Parameters** (beyond Namespace/Environment):

| Parameter | Classification | Default | Description |
|-----------|---------------|---------|-------------|
| LogBucketDomainName | Wirable — Required | — | Log bucket domain name for access logs |
| BucketNameSuffix | Config | `web` | Suffix for S3 bucket name |

**Outputs**:

| Output | Typical Consumers |
|--------|------------------|
| AppUrl | Post-deploy (configure-frontend, update-cognito-callback, update-backend-cors) |
| DistributionId | Post-deploy (invalidate-cf) |
| DistributionDomainName | Reference |
| BucketName | Post-deploy (upload-frontend) |

**Internal composition**: S3↔CloudFront OAC, bucket policy scoped to distribution ARN — all within the template.

---

#### ipa-stack-queue (Lifecycle: deploy)

**Suffix**: `queue` | **Capabilities**: CAPABILITY_NAMED_IAM | **Tier**: queue

Consolidated queue tier: SQS + DLQ + worker Lambda + ESM + DynamoDB (feature-flagged) + CloudWatch dashboard.

**Parameters** (beyond Namespace/Environment):

| Parameter | Classification | Default | Description |
|-----------|---------------|---------|-------------|
| ImageUri | Wirable — Required | — | ECR image URI with tag |
| AuthIssuer | Wirable — Required | — | Cognito OIDC issuer URL |
| AuthAudience | Wirable — Required | — | Cognito app client ID |
| QueueName | Config | `jobs` | Logical queue name |
| VisibilityTimeout | Config | `300` | Message visibility timeout (seconds) |
| MessageRetentionPeriod | Config | `345600` | Message retention (seconds, default 4 days) |
| MaxReceiveCount | Config | `3` | Attempts before DLQ |
| CreateDLQ | Feature Flag | `true` | Create dead-letter queue |
| FunctionName | Config | `fn-worker` | Worker Lambda name |
| MemorySize | Config | `512` | Worker Lambda memory (MB) |
| Timeout | Config | `300` | Worker Lambda timeout (seconds) |
| ImageCommand | Config | `python,-m,sqs_handler` | Worker container CMD |
| EnableJobsTable | Feature Flag | `false` | Create jobs DynamoDB table |
| AlarmSnsTopicArn | Wirable — Optional | *(empty)* | SNS topic for alarm actions |

**Feature Flags:**

| Flag | Default | Controls |
|------|---------|----------|
| EnableJobsTable | `false` | JobsTable resource, DynamoDB IAM policy, JobsTableArn output |
| CreateDLQ | `true` | DeadLetterQueue resource, DlqUrl/DlqArn outputs, DLQ depth alarm |

**Outputs**:

| Output | Typical Consumers |
|--------|------------------|
| QueueUrl | ipa-stack-backend (SqsQueueUrl) |
| QueueArn | ipa-stack-backend (SqsSendQueueArns) |
| QueueName | Reference |
| WorkerFunctionArn | Monitoring |
| WorkerFunctionName | Monitoring |
| DlqUrl | Conditional (HasDLQ) |
| DlqArn | Conditional (HasDLQ) |
| JobsTableArn | Conditional (HasJobsTable) |
| DashboardUrl | Observability |

**Internal composition**: SQS↔worker Lambda ESM, Lambda↔DynamoDB, Lambda↔CloudWatch, SQS↔DLQ — all connected within the template.

**Deploy ordering**: Queue deploys **before** backend when both are composed together (backend receives queue outputs via wirable parameters).

---

### Prepare Stacks

#### ipa-stack-cognito (Lifecycle: prepare)

**Suffix**: `cognito` | **Capabilities**: none

**Parameters** (beyond Namespace/Environment):
- CallbackURL (Config, default: `http://localhost:8080/authentication/callback`)
- CognitoDomainPrefix (Config, derived from APP_NAMESPACE + APP_ENV + account hash)
- MinPasswordLength (Config, default: 8)
- DeletionProtection (Config, default: INACTIVE)

**Outputs**:

| Output | Typical Consumers |
|--------|------------------|
| UserPoolId | Admin operations |
| UserPoolArn | Security policy scoping |
| UserPoolClientId | ipa-stack-backend (AuthAudience), ipa-stack-queue (AuthAudience) |
| IssuerUrl | ipa-stack-backend (AuthIssuer), ipa-stack-queue (AuthIssuer) |
| EndSessionEndpoint | Frontend OIDC config |
| HostedUIURL | Runbook reference |
| CognitoDomain | Frontend OIDC authority |
| DiscoveryUrl | JWT validation libraries |

---

#### ipa-stack-ecr (Lifecycle: prepare)

**Suffix**: `ecr` | **Capabilities**: none

**Parameters**: Namespace, Environment only.

**Outputs**:

| Output | Typical Consumers |
|--------|------------------|
| RepositoryUri | ipa-stack-backend (ImageUri), ipa-stack-queue (ImageUri) |
| RepositoryArn | Security policy scoping |

