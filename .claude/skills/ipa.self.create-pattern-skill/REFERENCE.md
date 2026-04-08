# Pattern Reference

Structural contracts, templates, and conventions for IPA deployment patterns. Load this file at the start of pattern authoring — all sections are needed throughout the workflow.

---

## 1. PATTERN.md Structure

Every pattern PATTERN.md follows this exact section order. All sections are mandatory unless marked optional.

### H1 Title and Description

~~~markdown
# Pattern: {pattern-name}

{One paragraph: what this pattern deploys end-to-end, which AWS services it composes,
and what architectural style it follows (e.g., serverless, container-based).
Mention key capabilities like authentication, streaming, CDN, etc.}
~~~

- Pattern name is lowercase with hyphens (e.g., `react-rest-lambda`, `api-worker-queue`).
- Description should convey the full scope so a reader understands the architecture without reading further.

### Stack Sequence

Ordered list of stack skills that compose this pattern. This is the primary artifact that `ipa.compose` parses.

~~~markdown
## Stack Sequence

1. ipa.stack.{service1} (prepare) — {one-line purpose}
   - Depends on: none
   - Suffix: {suffix}

2. ipa.stack.{service2} — {one-line purpose}
   - Depends on: ipa.stack.{service1}
   - Suffix: {suffix}
   - Config: {Key1}={Value1} {Key2}={Value2}
~~~

**Format rules:**

| Element | Format | Required | Notes |
|---------|--------|----------|-------|
| Number | `N.` or `Na.` | Yes | Sequential. Use `Na.` for stacks at same dependency level as `N` (e.g., `5a.` runs parallel with `5.`) |
| Stack reference | `ipa.stack.{service}` | Yes | Must match an existing skill directory name |
| Lifecycle | `(prepare)` | No | Placed between stack reference and em-dash. Omit for deploy lifecycle |
| Description | `— {text}` | Yes | One-line purpose after em-dash |
| Depends on | `- Depends on: {list}` | Yes | Comma-separated `ipa.stack.{service}` references, or `none` |
| Suffix | `- Suffix: {suffix}` | Yes | Stack name suffix for `{APP_NAMESPACE}-{APP_ENV}-{suffix}` |
| Config | `- Config: {Key}={Value} ...` | No | Space-separated parameter overrides. Only for parameters that differ from stack defaults |

**Lifecycle classification:**

| Lifecycle | Annotation | Makefile Target | Teardown Behavior |
|-----------|-----------|-----------------|-------------------|
| **prepare** | `(prepare)` | `scripts/prepare.mk` | Manual only — never auto-deleted by `/ipa.destroy` |
| **deploy** | (none) | `scripts/deploy.mk` | Automatic — deleted in reverse order by `/ipa.destroy` |

Use `(prepare)` for one-time prerequisites that should survive teardown: authentication providers (Cognito), container registries (ECR), and similar foundational resources. Use deploy (default) for application stacks that are created and destroyed together.

**Dependency rules:**
- Every stack must declare `Depends on:` — use `none` for stacks with no upstream dependencies.
- Dependencies must reference stacks that appear earlier in the sequence (no forward references).
- Circular dependencies are invalid — compose validation (V5) rejects them.
- `(prepare)` stacks can be depended on by deploy stacks, but prepare stacks themselves should not depend on deploy stacks.
- Parallel stacks (same number, e.g., `5.` and `5a.`) must not depend on each other.

**Suffix rules:**
- Must be unique across all stacks in the pattern.
- Defaults to the service name (e.g., `cognito`, `ecr`, `s3`).
- Multi-instance stacks use extended suffixes (e.g., `ddb-passengers`, `fn-stream`).
- Suffix is used in stack name: `{APP_NAMESPACE}-{APP_ENV}-{suffix}`.

### Teardown Sequence

Exact reverse of the deploy-lifecycle stacks in Stack Sequence. Prepare stacks are excluded.

~~~markdown
## Teardown Sequence

1. ipa.stack.{last-deploy} (suffix: {suffix})
2. ipa.stack.{second-to-last} (suffix: {suffix})
...
N. ipa.stack.{first-deploy} (suffix: {suffix})
~~~

**Rules:**
- Include only deploy-lifecycle stacks (exclude all `(prepare)` stacks).
- Order is exact reverse of Stack Sequence deployment order.
- Parallel stacks (e.g., `5.` and `5a.`) appear at the same position in teardown (reverse of their deploy position).
- Each entry includes `(suffix: {suffix})` for unambiguous identification.

### Wiring

YAML code block defining how stack outputs connect to stack parameters. This is the authoritative wiring declaration — `ipa.compose` uses it to generate `$(eval)` lines in Makefiles.

~~~markdown
## Wiring

```yaml
wiring:
  # {Source Stack} → {Target Stack} — {purpose}
  - source:
      stack: {source-suffix}
      output: {OutputKey}
    target:
      stack: {target-suffix}
      parameter: {ParameterName}
    notes: "{Description of what this wiring achieves}"
```
~~~

**Format rules:**

| Field | Value | Notes |
|-------|-------|-------|
| `source.stack` | Stack suffix (not full `ipa.stack.{service}` name) | e.g., `ecr`, `cognito`, `fn` |
| `source.output` | Output key from source stack's SKILL.md Outputs table | Must exist in the source stack |
| `target.stack` | Stack suffix | e.g., `fn`, `apigwv2`, `cf` |
| `target.parameter` | Parameter name from target stack's SKILL.md Parameters table | Must exist in the target stack |
| `notes` | Human-readable description | Explains the architectural purpose of this connection |

**Wiring conventions:**
- Comment lines (`# ...`) above each entry document the connection direction.
- Group wiring entries by source stack for readability.
- Every Wirable — Required parameter in a target stack should have a corresponding wiring entry (otherwise it's unresolved).
- Wirable — Optional parameters may be left unwired (the target stack handles the empty case via Conditions).
- Convention-based connections (e.g., App CloudWatch reads log group names by convention, not wiring) should be documented as YAML comments, not as wiring entries.

### Known Deferrals

~~~markdown
## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| {PREFIX}-{N} | {what is deferred} | {why — typically POC scope or service limitation} |
~~~

**Rules:**
- ID format: `{STACK_PREFIX}-{N}` where prefix is an uppercase abbreviation of the stack (e.g., `APIGW-1`, `CF-2`, `S3-1`).
- IDs must be unique within the pattern.
- Every deferral must have both Finding and Rationale populated.
- Deferrals flow into `scripts/SECURITY-DISPOSITION.md` when composed.

### Post-Deploy (Optional)

Operational steps that run after all stacks are deployed. Include only if the pattern requires post-deployment wiring (e.g., frontend config generation, CORS updates, data loading).

~~~markdown
## Post-Deploy

Steps that run after all stacks are successfully deployed. These are operational
steps (not CloudFormation stacks) that wire deployed infrastructure together.
Post-deploy runs automatically within /ipa.deploy — no separate invocation needed.

### {step-name}
- Action: {what this step does}
- Script: {script path or command}
- Depends on: {other post-deploy step names, or "(none within post-deploy)"}
- Stack outputs:
  - {suffix} → {OutputKey}
- .env variables: {comma-separated variable names from .env}
- Command: {exact command to run}
- Notes: {additional context}
~~~

**Format rules for each step:**

| Field | Required | Notes |
|-------|----------|-------|
| Action | Yes | One-line description of what this step does |
| Script | No | Path to script if step uses one (e.g., `scripts/util/configure_frontend.py`) |
| Depends on | Yes | Other post-deploy step names, or `(none within post-deploy)` |
| Stack outputs | No | Stack suffix → OutputKey pairs that this step needs to fetch |
| .env variables | No | Variables read from `.env` (not fetched from CloudFormation) |
| Command | No | Exact command if not a script (e.g., `aws s3 sync ...`) |
| Notes | No | Idempotency guarantees, parameter pass-through requirements, etc. |

**Key conventions:**
- Steps that update existing CloudFormation stacks (e.g., `update-cognito-callback`) must pass ALL original parameters plus the updated parameter. Note this explicitly.
- Cognito OIDC variables (OIDC_ISSUER, OIDC_CLIENT_ID, etc.) are referenced from `.env` — they are written by `prepare-cognito-env` in prepare.mk, not fetched via CloudFormation describe-stacks.
- Steps execute in dependency order. Steps with no mutual dependencies can run in parallel.

---

## 2. ARCHITECTURE.md Structure

Architecture reference document providing a visual and tabular overview of the pattern.

### Header

~~~markdown
# Architecture: {pattern-name} Pattern

{One sentence: what kind of application this pattern deploys.}
~~~

### System Architecture

ASCII layer diagram showing the dependency flow from top (user-facing) to bottom (foundational):

~~~markdown
## System Architecture

```text
Layer N:  [Top-level service] ──▶ {downstream1} (purpose), {downstream2} (purpose)
Layer 1:  [Middle service]    ──▶ {downstream} (purpose)
Layer 0:  [Foundation1]  [Foundation2]  [Foundation3]
```
~~~

**Conventions:**
- Layer 0 is foundational (no downstream dependencies).
- Higher layers depend on lower layers.
- Use `──▶` for dependency arrows.
- Group services at the same layer with brackets `[Service]`.
- Parenthetical notes describe the purpose of each connection.

### Stack Inventory

~~~markdown
## Stack Inventory

| Stack | Layer | Purpose | Status |
|-------|-------|---------|--------|
| ipa.stack.{service} | {N} | {purpose} | {Implemented / Pending} |
~~~

- Status: `**Implemented**` (bold) for stacks that have existing skill + CFN template. `Pending` for planned stacks.

### Deployment Order

~~~markdown
## Deployment Order

Stacks deploy bottom-up (Layer 0 → {N}). Within a layer, stacks have no mutual
dependencies and can deploy in parallel. Teardown is reverse order (Layer {N} → 0).
~~~

Include any notes about the current implementation state if the pattern is being built incrementally.

### Security Model

~~~markdown
## Security Model

- {Security principle 1}
- {Security principle 2}
- {Documented exceptions with references to SECURITY.md files}
~~~

Standard principles to include:
- No wildcard IAM ARNs — all permissions scoped to specific resource ARNs
- Each stack owns its own IAM (composability principle)
- No public resources by default
- Manual teardown for stateful resources (prevents accidental data loss)
- Document any exceptions (e.g., `ecr:GetAuthorizationToken` on `*` — AWS API limitation)

### Deployment Assumptions

~~~markdown
## Deployment Assumptions

- AWS credentials configured with Builder Execution Role permissions
- `.env` file with `APP_NAMESPACE` and `APP_ENV` set
- {tool} installed for {purpose}
- `/ipa.compose` generates Makefiles from this pattern
- Single-environment POC scope (no multi-account or multi-region)
~~~

---

## 3. ipa.compose Compatibility

For `ipa.compose` to process a pattern, it must pass V2 (pattern validation) and V4 (wiring validation).

### V2: Pattern Validation

| Check | Requirement |
|-------|-------------|
| Stack Sequence exists | `## Stack Sequence` heading present |
| At least one stack | Stack Sequence references at least one `ipa.stack.*` |
| Wiring section exists | `## Wiring` heading present with YAML code block |
| ARCHITECTURE.md exists | File present in pattern directory |
| Teardown Sequence exists | `## Teardown Sequence` heading present |

### V4: Wiring Map Validation

| Check | Requirement |
|-------|-------------|
| Source output exists | `source.output` matches an entry in source stack's SKILL.md Outputs table |
| Target parameter exists | `target.parameter` matches an entry in target stack's SKILL.md Parameters table |
| No circular dependencies | Wiring graph is acyclic |
| Source stack in pattern | `source.stack` suffix matches a stack in Stack Sequence |
| Target stack in pattern | `target.stack` suffix matches a stack in Stack Sequence |

### How Compose Reads Patterns

1. **Stack Sequence** — parsed as numbered list. Each entry extracts: stack reference, lifecycle (`prepare` or `deploy`), dependencies, suffix, optional config overrides.
2. **Wiring** — parsed as YAML inside a code fence. Each entry maps `source.stack + source.output` to `target.stack + target.parameter`.
3. **Teardown Sequence** — parsed as numbered list. Validates it is the exact reverse of deploy-lifecycle stacks.
4. **Known Deferrals** — parsed into SECURITY-DISPOSITION.md as Pattern Deferrals.
5. **Post-Deploy** — each H3 subsection becomes a target in `post-deploy.mk`.

---

## 4. Available Stack Inventory

Stack skills available for pattern composition. Use this to select stacks and plan wiring.

### ipa.stack.cognito (Lifecycle: prepare)

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
| UserPoolArn | ipa.stack.apigw (CognitoUserPoolArn) |
| UserPoolClientId | ipa.stack.lambda (AuthAudience), ipa.stack.apigwv2 (UserPoolClientId) |
| IssuerUrl | ipa.stack.lambda (AuthIssuer), ipa.stack.apigwv2 (IssuerUrl) |
| EndSessionEndpoint | Frontend OIDC config |
| HostedUIURL | Runbook reference |
| CognitoDomain | Frontend OIDC authority |
| DiscoveryUrl | JWT validation libraries |

---

### ipa.stack.ecr (Lifecycle: prepare)

**Suffix**: `ecr` | **Capabilities**: none

**Parameters**: Namespace, Environment only.

**Outputs**:
| Output | Typical Consumers |
|--------|------------------|
| RepositoryUri | ipa.stack.lambda (ImageUri) |
| RepositoryArn | Security policy scoping |

---

### ipa.stack.dynamodb (Lifecycle: deploy)

**Suffix**: `ddb` or `ddb-{model}` (multi-instance) | **Capabilities**: none

**Parameters** (beyond Namespace/Environment):
- TableName (Pattern-provided, from `APP_DDB_TABLE_{MODEL}`)
- PartitionKey (Config, default: `id`)
- BillingMode (Config, default: `PAY_PER_REQUEST`)

**Outputs**:
| Output | Typical Consumers |
|--------|------------------|
| TableArn | ipa.stack.lambda (DynamoDbTableArns) |

---

### ipa.stack.lambda (Lifecycle: deploy)

**Suffix**: `{fn-name}` (e.g., `fn`, `fn-stream`) | **Capabilities**: CAPABILITY_NAMED_IAM

**Parameters** (beyond Namespace/Environment):
- FunctionName (Pattern-provided)
- InvokeMode (Config: `BUFFERED` or `RESPONSE_STREAM`)
- MemorySize (Config, default: 512)
- Timeout (Config, default: 30)
- LogBucketName (Wirable — Optional, from ipa.security)
- ImageUri (Wirable — Required, from ecr RepositoryUri)
- AuthIssuer (Wirable — Required, from cognito IssuerUrl)
- AuthAudience (Wirable — Required, from cognito UserPoolClientId)
- DynamoDbTableArns (Wirable — Optional, from dynamodb TableArn)

**Outputs**:
| Output | Typical Consumers |
|--------|------------------|
| FunctionArn | ipa.stack.apigw/apigwv2 (LambdaFunctionArn) |
| FunctionName | Monitoring, invoke commands |
| ExecutionRoleArn | Security auditing |

**Build Requirements**: container image from ECR (Dockerfile path in skill).

---

### ipa.stack.apigw (Lifecycle: deploy)

**Suffix**: `apigw` | **Capabilities**: none

REST API Gateway v1 with Cognito authorizer.

**Key Wirable Parameters**: CognitoUserPoolArn, LambdaFunctionArn, StreamingLambdaFunctionArn (optional)
**Key Outputs**: ApiUrl, ApiId

---

### ipa.stack.apigwv2 (Lifecycle: deploy)

**Suffix**: `apigwv2` | **Capabilities**: none

HTTP API Gateway v2 with JWT authorizer and SSE streaming routes.

**Key Wirable Parameters**: LambdaFunctionArn, IssuerUrl, UserPoolClientId, StreamingLambdaFunctionArn (optional)
**Key Outputs**: ApiUrl, ApiId

---

### ipa.stack.s3 (Lifecycle: deploy)

**Suffix**: `s3` | **Capabilities**: none

**Key Wirable Parameters**: LogBucketName (from ipa.security)
**Key Outputs**: BucketName, BucketArn, BucketDomainName

---

### ipa.stack.cloudfront (Lifecycle: deploy)

**Suffix**: `cf` | **Capabilities**: none

**Key Wirable Parameters**: S3BucketDomainName, S3BucketArn, S3BucketName, ApiGatewayUrl (optional), LogBucketName (optional)
**Key Outputs**: DistributionId, DistributionDomainName, AppUrl

---

### ipa.stack.app-cloudwatch (Lifecycle: deploy)

**Suffix**: `cw` or `app-cloudwatch` | **Capabilities**: none

Convention-based — reads log group names from Namespace + Environment. No explicit wiring needed for standard deployments.

**Key Config Parameters**: LambdaFunctionNames, ApiGatewayName, various thresholds
**Key Outputs**: DashboardName

---

## 5. Wiring Design Guidance

### Auto-Wiring vs Explicit Wiring

`ipa.compose` attempts auto-wiring by exact name match (output name == parameter name). The pattern's Wiring section provides explicit wiring that overrides auto-inference.

**When parameter name matches output name** (e.g., `BucketArn` output → `BucketArn` parameter):
- Auto-wiring handles this. Still declare it in the pattern's Wiring section for documentation and to make the connection authoritative.

**When names differ** (e.g., `IssuerUrl` output → `AuthIssuer` parameter):
- Must be declared in the pattern's Wiring section. Auto-wiring will not resolve this.

### Convention-Based Connections

Some stacks connect by naming convention rather than explicit wiring:
- **App CloudWatch** constructs log group names from `Namespace + Environment` — no wiring entry needed.
- **DynamoDB runtime access** — Lambda resolves table names via `PynamodbUtil.env_table_name()` convention. The wiring only provides `TableArn` for IAM policy scoping, not for table name resolution.

Document convention-based connections as YAML comments in the Wiring section:

~~~yaml
  # Lambda → App CloudWatch — no explicit wiring needed
  # App CloudWatch constructs log group names by convention from Namespace + Environment
~~~

### Multi-Instance Stack Wiring

When a stack is deployed multiple times (e.g., multiple DynamoDB tables):
- Each instance has a unique suffix (e.g., `ddb-passengers`, `ddb-jobs`).
- Wiring entries reference the specific suffix, not the generic stack name.
- If multiple instances wire to the same target parameter (e.g., multiple TableArns → Lambda DynamoDbTableArns), compose concatenates the values with commas.
