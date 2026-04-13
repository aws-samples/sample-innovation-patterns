---
name: ipa.quickstart
description: "Deploy a full-stack IPA pattern with one command. Handles init, security,
  compose, and deploy with smart defaults. Use when the user says 'quickstart',
  'quick deploy', 'set up everything', or invokes /ipa.quickstart."
model: opus
---

# /ipa.quickstart — One-Command Full-Stack Deployment

This skill orchestrates the complete IPA lifecycle — init, security, compose, prepare, build, deploy, and post-deploy — with a single prompt. It gathers only the project namespace, applies convention-over-configuration defaults for everything else, and drives through the entire workflow end-to-end.

**Default pattern**: `react-rest-lambda` (frontend + backend). Optional: `sqs-lambda` (queue tier add-on).

> **AWS credential resolution**: All `aws` CLI commands must be prefixed with `source .env 2>/dev/null;` to load credentials into the environment. Do NOT pass `--profile` or `--region` flags explicitly.

---

## What This Skill Does

1. Detects existing project state (idempotent re-runs)
2. Gathers namespace + optional queue selection (1 prompt)
3. Writes `.env` with smart defaults (inline init — no prompts)
4. Deploys security stack with AdministratorAccess (inline security — no prompts)
5. Generates Makefiles (delegates to `/ipa.compose` — no prompts)
6. Builds and deploys all stacks via Make targets directly (no confirmation prompt)
7. Reports results with endpoints and next steps

## What This Skill Does NOT Do

- Does not replace individual skills — use `/ipa.init`, `/ipa.security`, `/ipa.compose`, `/ipa.deploy` for fine-grained control
- Does not support the existing-role-ARN path — use `/ipa.security` for that
- Does not support teardown — use `/ipa.destroy`
- Does not support custom patterns — hardcoded to `react-rest-lambda` with optional `sqs-lambda`
- Does not support custom regions, environments, or profiles — defaults to `us-east-1`, `dev`, default credential chain
- Does not modify `.env` variables set by other tools — preserves non-IPA content

## Information Sources

| Source | What Quickstart Reads | When |
|--------|----------------------|------|
| `.env` | IPA variables (APP_NAMESPACE, APP_ENV, etc.) | State detection (Step 0) |
| `.claude/skills/ipa.init/SKILL.md` | Validation Rules section | Namespace validation (Step 1) |
| `.claude/skills/ipa.security/SKILL.md` | Step 6a security template, Validation Rules | Security template + policy validation (Step 3) |
| `scripts/deploy.mk` | File existence | Compose state detection (Step 0) |
| `source .env 2>/dev/null; aws cloudformation describe-stacks` | Stack status | Security + prepare state detection |
| `source .env 2>/dev/null; aws sts get-caller-identity` | Account ID, credential validity | Account detection (Step 2), pre-flight (Step 5) |

---

## Step 0: State Detection

Before any prompting, check existing project state to support idempotent re-runs.

### 0.1 Check .env

Read `.env` at the project root. Look for `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_ACCOUNT_ID`.

- **If `.env` exists with all 4 variables set and non-empty**: set `init_complete = true`. Store the values. Display: "Detected existing project: `{APP_NAMESPACE}-{APP_ENV}` in `{AWS_REGION}`"
- **If `.env` is missing or any of the 4 variables are absent/empty**: set `init_complete = false`.

### 0.2 Check Security Stack

If `init_complete = true`:

Run:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name $(grep APP_NAMESPACE .env | cut -d= -f2)-$(grep APP_ENV .env | cut -d= -f2)-security \
  --query 'Stacks[0].StackStatus' --output text
```

- **Status is `CREATE_COMPLETE` or `UPDATE_COMPLETE`**: set `security_complete = true`.
- **Any other status or command fails**: set `security_complete = false`.

If `init_complete = false`: set `security_complete = false`.

### 0.3 Check Makefiles

If `init_complete = true`:

Check if `scripts/deploy.mk` exists at the project root.

- **If exists**: set `compose_complete = true`.
- **If missing**: set `compose_complete = false`.

If `init_complete = false`: set `compose_complete = false`.

### 0.4 Determine Flow

Route to the appropriate step based on detected state:

| init_complete | security_complete | compose_complete | Action |
|---------------|-------------------|------------------|--------|
| false | — | — | Start from **Step 1** (full lifecycle) |
| true | false | — | Skip to **Step 3** (security onward) |
| true | true | false | Skip to **Step 4** (compose onward) |
| true | true | true | Display: "All steps already complete. Re-running deploy (idempotent)..." → Skip to **Step 5** |

---

## Step 1: Gather Input

> **Skip this step if `init_complete = true`.** Use existing `.env` values for all subsequent steps.

Use a SINGLE `AskUserQuestion` call with 2 questions:

1. **APP_NAMESPACE** (header: "Namespace", multiSelect: false)
   - Question: "Choose a project namespace. All stacks use `{namespace}-dev-*` naming. (1-12 chars, lowercase letters/digits/hyphens, starts with letter)"
   - Options:
     - **"app" (Recommended)** — "Default namespace — good for single-project accounts"
   - Other (built-in): builder types a custom namespace

2. **Include queue tier** (header: "Queue", multiSelect: false)
   - Question: "Include background job processing (SQS queue + worker Lambda)?"
   - Options:
     - **"No" (Recommended)** — "Frontend + backend only (deploys faster)"
     - **"Yes"** — "Add SQS queue tier for async job processing"

### Post-Prompt Validation

Validate `APP_NAMESPACE` per the rules in `.claude/skills/ipa.init/SKILL.md` → Validation Rules section:

- Pattern: `/^[a-z][a-z0-9-]{0,11}$/`
- Must NOT start or end with a hyphen
- Must NOT contain consecutive hyphens (`--`)
- Error message: "Invalid namespace — must be 1-12 chars, lowercase letters/digits/hyphens, must start with a letter"

If invalid: display the error and re-prompt for namespace only using a simple text prompt (not AskUserQuestion). Do NOT re-ask the queue question.

Store results:
- `namespace` — the validated namespace value
- `include_queue` — boolean (`true` if "Yes" selected, `false` otherwise)

---

## Step 2: Write .env (Inline Init)

> **Skip if `init_complete = true`.**

### 2.1 Auto-Detect Account ID

Run:
```bash
aws sts get-caller-identity --query Account --output text
```

- **If succeeds**: store result as `account_id`. Display: "Detected AWS Account: `{account_id}`"
- **If fails** (AWS CLI not installed, invalid credentials, or any error): silently fall back to manual prompt. Display: "AWS account ID could not be auto-detected. Enter your 12-digit AWS Account ID:" Validate: `/^\d{12}$/`. If invalid, display "Invalid account ID — must be exactly 12 digits" and re-prompt.

### 2.2 Write .env

Write `.env` at the project root. If `.env` already exists, preserve all non-IPA lines (lines that are not IPA-managed variables or IPA header comments). Write the IPA block at the top:

```
# IPA Project Configuration
# Generated by /ipa.quickstart — local only, do not commit
AWS_REGION=us-east-1
AWS_ACCOUNT_ID={account_id}
APP_NAMESPACE={namespace}
APP_ENV=dev
APP_CODE_AGENT=claude-code
APP_IAC=cloudformation
```

Note: `AWS_PROFILE` is intentionally omitted — uses default AWS credential chain.

### 2.3 Write .env.example

Follow the `.env.example` template from `.claude/skills/ipa.init/SKILL.md` → `.env.example Generation` section. Use **section-based update**: if `.env.example` exists and contains a `# IPA Project Configuration Template` header, replace only that section. If the header does not exist, write the template as the entire file. Preserve all other sections (e.g., `# IPA Security Configuration`).

Display: "Configuration written to `.env`"

---

## Step 3: Deploy Security Stack (Inline Security)

> **Skip if `security_complete = true`.** On skip, display: "Security stack already deployed. Skipping."

### 3.1 Write Security Template

Create the directory if it does not exist:
```bash
mkdir -p infra/cfn/generated
```

Write the managed-policy-path security template from `.claude/skills/ipa.security/SKILL.md` → Step 6a to `infra/cfn/generated/security.yml`. Copy the template exactly as specified in the security skill — do not modify it.

### 3.2 Deploy

Display: "Deploying security stack (`{namespace}-dev-security`)..."

Run:
```bash
source .env 2>/dev/null; aws cloudformation deploy \
  --template-file infra/cfn/generated/security.yml \
  --stack-name {namespace}-dev-security \
  --parameter-overrides \
    Namespace={namespace} \
    Environment=dev \
    AccountId={account_id} \
    Region=us-east-1 \
    ManagedPolicyArn=arn:aws:iam::aws:policy/AdministratorAccess \
    KmsKeyArn="" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

Where `{namespace}` and `{account_id}` are the values from Step 1/2 (or from `.env` if init was skipped).

### 3.3 Handle Failure

If the deploy command fails:

1. Read stack events to diagnose:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stack-events \
     --stack-name {namespace}-dev-security \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
     --output table
   ```

2. **If the error mentions "policy", "ManagedPolicyArn", or "does not exist"**:
   - Display: "`AdministratorAccess` policy is not available in this account. Enter a managed policy name or full ARN (e.g., `PowerUserAccess` or `arn:aws:iam::aws:policy/PowerUserAccess`):"
   - Validate per `.claude/skills/ipa.security/SKILL.md` → Validation Rules section (accepts short names, AWS-managed ARNs, and customer-managed ARNs)
   - If short name provided: resolve to `arn:aws:iam::aws:policy/{name}`
   - Re-deploy with the provided policy ARN

3. **If the stack is in `ROLLBACK_COMPLETE`** state:
   - Display: "Security stack is in ROLLBACK_COMPLETE from a previous failure. Deleting and retrying..."
   - Run: `source .env 2>/dev/null; aws cloudformation delete-stack --stack-name {namespace}-dev-security`
   - Wait: `source .env 2>/dev/null; aws cloudformation wait stack-delete-complete --stack-name {namespace}-dev-security`
   - Retry the deploy from Step 3.2.

4. **Other errors**: Display the error details and STOP with: "Security deployment failed. Run `/ipa.security` for interactive diagnosis."

### 3.4 Write Security Variables to .env

After successful deployment, retrieve stack outputs:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {namespace}-dev-security \
  --query 'Stacks[0].Outputs' --output json
```

Extract `BuilderRoleArn` and `CodeBuildRoleArn` from the outputs.

Append to `.env` using **section-based update**: if a `# IPA Security Configuration` header exists, replace that block. Otherwise append after the last line with a blank line separator:

```
# IPA Security Configuration
# Generated by /ipa.quickstart — local only, do not commit
APP_BUILDER_ROLE_ARN={BuilderRoleArn from stack output}
APP_CODEBUILD_ROLE_ARN={CodeBuildRoleArn from stack output}
```

Display: "Security stack deployed. IAM roles provisioned."

---

## Step 4: Compose Pattern (Delegate to /ipa.compose)

> **Skip if `compose_complete = true`.** On skip, display:
> "Makefiles already exist (`scripts/deploy.mk`). Skipping compose. To regenerate, run `/ipa.compose` manually."

### 4.1 Determine Pattern Arguments

- If `include_queue = false` (or not set because init was skipped): pattern args = `react-rest-lambda`
- If `include_queue = true`: pattern args = `react-rest-lambda sqs-lambda`

### 4.2 Invoke Compose

Display: "Composing `{pattern args}` pattern..."

Invoke `/ipa.compose {pattern args}` using the Skill tool.

Compose auto-proceeds without confirmation (per compose SKILL.md Step 5 — "Do NOT ask for confirmation"). Wait for compose to complete. It generates:
- `scripts/prepare.mk`, `scripts/deploy.mk`, `scripts/build.mk`, `scripts/post-deploy.mk`, `scripts/env.mk`, `scripts/test.mk`
- `scripts/SECURITY-DISPOSITION.md`

Display: "Composition complete. Makefiles generated."

---

## Step 5: Build and Deploy

No confirmation prompt — the builder confirmed intent by invoking `/ipa.quickstart`.

### 5.1 Pre-Flight Validation

Verify all prerequisites. Run all checks and report all failures at once:

| Check | How | Error If Fails |
|-------|-----|----------------|
| `.env` has `APP_NAMESPACE` | Read `.env` | "Missing APP_NAMESPACE. This should not happen after init." |
| `.env` has `APP_ENV` | Read `.env` | "Missing APP_ENV." |
| `.env` has `AWS_REGION` | Read `.env` | "Missing AWS_REGION." |
| `.env` has `AWS_ACCOUNT_ID` | Read `.env` | "Missing AWS_ACCOUNT_ID." |
| `.env` has `APP_BUILDER_ROLE_ARN` | Read `.env` | "Missing APP_BUILDER_ROLE_ARN. Run `/ipa.security`." |
| `scripts/deploy.mk` exists | File check | "deploy.mk not found. Run `/ipa.compose`." |
| `scripts/build.mk` exists | File check | "build.mk not found. Run `/ipa.compose`." |
| AWS credentials valid | `source .env 2>/dev/null; aws sts get-caller-identity` | "AWS credentials invalid or expired." |
| GNU Make installed | `which make` | "GNU Make not installed." |

If **any** check fails: display all failures and **STOP** with: "Fix the above issues and re-run `/ipa.quickstart`."

### 5.2 Prepare (Auto-Trigger)

Check if prepare stacks need deployment. For each prepare stack referenced in `scripts/prepare.mk` (typically `cognito` and `ecr`):

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-cognito \
  --query 'Stacks[0].StackStatus' --output text
```

If **any** prepare stack does not exist or is not in a `*_COMPLETE` state:

Display: "Deploying prerequisite stacks (Cognito, ECR)..."

Run:
```bash
make -f scripts/prepare.mk prepare
```

Display Make output as it runs.

If prepare fails: display the error. **STOP** with: "Prepare failed. Run `/ipa.prepare` for interactive diagnosis."

### 5.3 Build

Display: "Building artifacts..."

Run:
```bash
make -f scripts/build.mk build
```

Display Make output as it runs. If `build.mk` has no real targets, the aggregate target outputs "No build targets" and exits 0 — this is expected.

If build fails (exit code != 0): display the full error output. **STOP** with: "Build failed. Check the output above. Retry: `make -f scripts/build.mk build`"

### 5.4 Deploy

Display: "Deploying stacks..."

Run:
```bash
make -f scripts/deploy.mk deploy
```

Display Make output as it runs.

If deploy fails (exit code != 0):
1. Identify the failed stack from the Make output (look for `--stack-name` in the failed command)
2. Read stack events:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stack-events \
     --stack-name {failed-stack-name} \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
     --output table
   ```
3. Display the diagnosis.
4. **STOP** with: "Deploy failed. Run `/ipa.deploy` for interactive recovery."

### 5.5 Verify

For each deploy stack (typically `backend` and `frontend`, plus `queue` if selected), verify status:

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-{suffix} \
  --query 'Stacks[0].StackStatus' --output text
```

Confirm all report `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

### 5.6 Post-Deploy

Check if `scripts/post-deploy.mk` exists.

If it exists and has non-no-op targets:

Display: "Running post-deploy wiring..."

Run:
```bash
make -f scripts/post-deploy.mk post-deploy
```

Display Make output as it runs.

If post-deploy fails: display the error. Advise: "Post-deploy failed. Deployed stacks are intact — no rollback needed. Fix the issue and retry: `make -f scripts/post-deploy.mk post-deploy`"

Do NOT roll back deployed CloudFormation stacks on post-deploy failure.

---

## Step 6: Completion Report

Collect stack outputs for the completion report:

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-frontend \
  --query 'Stacks[0].Outputs' --output json
```

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-backend \
  --query 'Stacks[0].Outputs' --output json
```

Display:

```
Quickstart Complete: {APP_NAMESPACE}-{APP_ENV}

  Pattern: react-rest-lambda [+ sqs-lambda]

  Stack                              Status
  ─────────────────────────────────  ───────────────
  {APP_NAMESPACE}-{APP_ENV}-security    deployed
  {APP_NAMESPACE}-{APP_ENV}-cognito     deployed
  {APP_NAMESPACE}-{APP_ENV}-ecr         deployed
  {APP_NAMESPACE}-{APP_ENV}-backend     deployed
  {APP_NAMESPACE}-{APP_ENV}-frontend    deployed
  [{APP_NAMESPACE}-{APP_ENV}-queue      deployed]

  Application URL: {AppUrl from frontend stack output}
  API URL: {ApiUrl from backend stack output}
  Cognito Login: {HostedUiUrl from cognito stack output}

What was deployed:
  - React frontend on CloudFront + S3
  - REST API on API Gateway v2 + Lambda (container)
  - Cognito authentication (OIDC)
  - DynamoDB data storage
  - CloudWatch observability dashboards
  [- SQS queue + worker Lambda (if queue was selected)]

Next steps:
  - Open the Application URL to access the deployed application
  - Run `/ipa.destroy` to tear down all deploy stacks
  - Run `/ipa.compose` to regenerate Makefiles if patterns change
  - Run `/ipa.deploy` for subsequent deployments (with confirmation prompt)
  - See the Composing a Solution guide for composition details
  - See the Path to Production guide for production readiness
```

Include the queue stack line only if `include_queue = true` or if the queue stack exists.

---

## Error Handling

### AWS Credential Errors

If any AWS CLI command fails with `ExpiredTokenException`, `ExpiredToken`, `InvalidClientTokenId`, or similar credential errors at any point during execution:

Display: "AWS credentials are not configured or have expired. Ensure your AWS CLI is configured (`aws configure`) or refresh your session (`aws sso login`)."

**STOP.** The builder must fix credentials before re-running `/ipa.quickstart`.

### Account ID Detection Failure

Handled in Step 2.1 — falls back to manual prompt. This is the ONLY additional interaction beyond Step 1.

### Security Policy Not Available

Handled in Step 3.3 — falls back to prompting for a policy name. Validates per the security skill's rules.

### ROLLBACK_COMPLETE on Any Stack

If any stack (security, prepare, or deploy) is detected in `ROLLBACK_COMPLETE`:

1. Display: "Stack `{name}` is in ROLLBACK_COMPLETE from a previous failure. Deleting and retrying..."
2. Delete: `source .env 2>/dev/null; aws cloudformation delete-stack --stack-name {name}`
3. Wait: `source .env 2>/dev/null; aws cloudformation wait stack-delete-complete --stack-name {name}`
4. Retry the step that encountered the failed stack.

### Make Failures

For build, deploy, and post-deploy Make failures, display the error output and advise the builder to use the individual skill for interactive diagnosis:

| Failure | Advice |
|---------|--------|
| `make -f scripts/prepare.mk prepare` fails | "Run `/ipa.prepare` for interactive diagnosis." |
| `make -f scripts/build.mk build` fails | "Check build output above. Retry: `make -f scripts/build.mk build`" |
| `make -f scripts/deploy.mk deploy` fails | "Run `/ipa.deploy` for interactive diagnosis and recovery." |
| `make -f scripts/post-deploy.mk post-deploy` fails | "Stacks are intact. Retry: `make -f scripts/post-deploy.mk post-deploy`" |

### General Pattern

The quickstart handles the happy path end-to-end. For error recovery beyond basic retries (ROLLBACK_COMPLETE deletion, policy fallback), fall back to the individual process skills (`/ipa.security`, `/ipa.deploy`) which have comprehensive interactive diagnosis and recovery flows.
