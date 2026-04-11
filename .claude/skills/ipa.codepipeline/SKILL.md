---
name: ipa.codepipeline
description: "Deploy a CI/CD pipeline (CodeCommit + CodePipeline) for automated build/test/deploy. Use when the user says 'pipeline', 'CI/CD', 'codepipeline', or invokes /ipa.codepipeline."
model: opus
---

# /ipa.codepipeline — Deploy CI/CD Pipeline

This skill deploys a CI/CD pipeline that runs the same `scripts/*.mk` Makefiles the builder runs locally. It creates a CodeCommit repository (for source code) and a CodePipeline (for automated build/test/deploy). The pipeline triggers automatically on code push.

> **AWS credential resolution**: All `aws` CLI commands must be prefixed with `source .env 2>/dev/null;` to load credentials into the environment. Do NOT pass `--profile` or `--region` flags explicitly.

---

## Variable Schema

The skill manages these variables in the `.env` file's `# IPA Pipeline Configuration` block:

| Variable | Set By | Description |
|----------|--------|-------------|
| `PIPELINE_STACK_NAME` | Computed | CodePipeline CloudFormation stack name |
| `PIPELINE_NAME` | Stack output | CodePipeline pipeline name |
| `CODEBUILD_PROJECT_NAME` | Stack output | CodeBuild project name |
| `CODECOMMIT_STACK_NAME` | Computed | CodeCommit CloudFormation stack name |
| `CODECOMMIT_REPO_NAME` | Stack output | CodeCommit repository name |
| `CODECOMMIT_CLONE_URL` | Stack output | HTTPS clone URL for the repository |

---

## Step 1: Pre-Flight Checks

Before any prompting, verify prerequisites and determine execution flow.

### 1.1 Verify `.env` Prerequisites

Read `.env` at the project root and check for these variables (written by `/ipa.init`):
- `APP_NAMESPACE`
- `APP_ENV`
- `AWS_ACCOUNT_ID`
- `AWS_REGION`

**If any are missing**: STOP with: "Cannot proceed — `.env` is missing required IPA variables. Run `/ipa.init` first to configure project defaults."

### 1.2 Verify Security Prerequisites

Check if `.env` contains `APP_CODEBUILD_ROLE_ARN`:

**If missing**: STOP with: "Cannot proceed — `APP_CODEBUILD_ROLE_ARN` is not set. Run `/ipa.security` first to provision the CodeBuild execution role."

### 1.3 Verify Compose Prerequisites

Check if `scripts/deploy.mk` exists at the project root:

**If missing**: STOP with: "Cannot proceed — `scripts/deploy.mk` not found. Run `/ipa.compose` first to generate Makefiles."

### 1.4 Verify Buildspec

Check if `buildspec.yml` exists at the project root:

**If missing**: STOP with: "Cannot proceed — `buildspec.yml` not found at the repository root. Create it before setting up the pipeline. See the IPA documentation for the standard buildspec template."

### 1.5 Detect Existing Pipeline Configuration

Check if `.env` contains `PIPELINE_STACK_NAME`:

- **If present** → route to the **Update Flow** (Step U1).
- **If absent** → continue to Step 1.6.

### 1.6 Check CloudFormation Stack Status

Compute the stack name: `{APP_NAMESPACE}-{APP_ENV}-codepipeline`

Run:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-codepipeline \
  --query 'Stacks[0].StackStatus' \
  --output text
```

- **Stack does not exist** → continue with **First-Time Flow** (Step 2).
- **Stack exists and NOT `ROLLBACK_COMPLETE`** → route to **Update Flow** (Step U1).
- **Stack in `ROLLBACK_COMPLETE`** → route to **ROLLBACK_COMPLETE Recovery** (Error Handling section).

---

## Step 2: Source Configuration

Use AskUserQuestion with 2 questions:

1. **Repository name** (header: "Repo Name", multiSelect: false)
   - Question: "What should the CodeCommit repository be named?"
   - Options:
     - **"{APP_NAMESPACE}-{APP_ENV}-repo" (Recommended)** — "Default naming convention"
   - The builder may accept the default or provide a custom name via "Other".
   - Validate: must match `[a-zA-Z0-9._-]+`

2. **Branch name** (header: "Branch", multiSelect: false)
   - Question: "Which branch should trigger the pipeline?"
   - Options:
     - **"main" (Recommended)** — "Standard default branch"
     - **"develop"** — "Development branch"
   - The builder may select an option or provide a custom branch name via "Other".

---

## Step 3: Query Prepare-Stack Outputs

Query the ECR and Cognito stacks for values needed as CodeBuild environment variables.

### 3.1 Query ECR Stack

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-ecr \
  --query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
  --output text
```

Store the result as `ECR_REPO_URI`.

**If the ecr stack does not exist**: STOP with: "Cannot proceed — the ECR stack `{namespace}-{env}-ecr` does not exist. Run `/ipa.prepare` first to deploy prerequisite stacks."

### 3.2 Query Cognito Stack

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-cognito \
  --query 'Stacks[0].Outputs' \
  --output json
```

Extract:
- `IssuerUrl` → `OIDC_ISSUER`
- `UserPoolClientId` → `OIDC_CLIENT_ID`
- `EndSessionEndpoint` → `OIDC_END_SESSION_ENDPOINT`

**If the cognito stack does not exist**: STOP with: "Cannot proceed — the Cognito stack `{namespace}-{env}-cognito` does not exist. Run `/ipa.prepare` first to deploy prerequisite stacks."

---

## Step 4: Confirmation Summary

Display a confirmation table before deployment:

```
┌────────────────────────┬─────────────────────────────────────────────────────────────┬───────────────┐
│ Setting                │ Value                                                       │ Source        │
├────────────────────────┼─────────────────────────────────────────────────────────────┼───────────────┤
│ Repository Name        │ {repo_name}                                                 │ prompted      │
│ Branch                 │ {branch}                                                    │ prompted      │
│ CodeBuild Role         │ {APP_CODEBUILD_ROLE_ARN}                                    │ from .env     │
│ Build Image            │ aws/codebuild/standard:7.0                                  │ default       │
│ Compute Type           │ BUILD_GENERAL1_LARGE                                        │ default       │
│ ECR Repo URI           │ {ecr_repo_uri}                                              │ ecr stack     │
│ OIDC Issuer            │ {oidc_issuer}                                               │ cognito stack │
│ CodeCommit Stack       │ {namespace}-{env}-codecommit                                │ computed      │
│ CodePipeline Stack     │ {namespace}-{env}-codepipeline                              │ computed      │
└────────────────────────┴─────────────────────────────────────────────────────────────┴───────────────┘
```

Use AskUserQuestion:
- Question: "Deploy this pipeline configuration?"
- Header: "Deploy"
- Options:
  - **"Yes, deploy"** — "Deploy both the CodeCommit and CodePipeline stacks"
  - **"No, start over"** — "Return to source configuration"
- multiSelect: false

- If **"Yes, deploy"** → proceed to Step 5.
- If **"No, start over"** → restart from Step 2.

---

## Step 5: Deploy CodeCommit Stack

```bash
source .env 2>/dev/null; aws cloudformation deploy \
  --template-file infra/cfn/codecommit/codecommit.yml \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-codecommit \
  --parameter-overrides \
    Namespace={APP_NAMESPACE} \
    Environment={APP_ENV} \
    RepositoryName={repo_name} \
    RepositoryDescription="IPA-managed source repository" \
    KmsKeyArn="" \
  --no-fail-on-empty-changeset
```

Wait for completion. If it fails, proceed to Error Handling.

---

## Step 6: Deploy CodePipeline Stack

```bash
source .env 2>/dev/null; aws cloudformation deploy \
  --template-file infra/cfn/codepipeline/codepipeline.yml \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-codepipeline \
  --parameter-overrides \
    Namespace={APP_NAMESPACE} \
    Environment={APP_ENV} \
    AccountId={AWS_ACCOUNT_ID} \
    CodeBuildRoleArn={APP_CODEBUILD_ROLE_ARN} \
    SourceRepoName={repo_name} \
    SourceBranch={branch} \
    EcrRepoUri={ECR_REPO_URI} \
    OidcIssuer={OIDC_ISSUER} \
    OidcClientId={OIDC_CLIENT_ID} \
    OidcEndSessionEndpoint={OIDC_END_SESSION_ENDPOINT} \
    BuildImage=aws/codebuild/standard:7.0 \
    ComputeType=BUILD_GENERAL1_LARGE \
    KmsKeyArn="" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

Wait for completion. If it fails, proceed to Error Handling.

---

## Step 7: Write .env Pipeline Variables

### 7.1 Retrieve Stack Outputs

Query the codepipeline stack outputs:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-codepipeline \
  --query 'Stacks[0].Outputs' \
  --output json
```

Extract: `PipelineName`, `CodeBuildProjectName`.

Query the codecommit stack outputs:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-codecommit \
  --query 'Stacks[0].Outputs' \
  --output json
```

Extract: `RepositoryName`, `CloneUrlHttp`.

### 7.2 Compose .env Pipeline Block

```
# IPA Pipeline Configuration
# Generated by /ipa.codepipeline — local only, do not commit
PIPELINE_STACK_NAME={APP_NAMESPACE}-{APP_ENV}-codepipeline
PIPELINE_NAME={from stack output PipelineName}
CODEBUILD_PROJECT_NAME={from stack output CodeBuildProjectName}
CODECOMMIT_STACK_NAME={APP_NAMESPACE}-{APP_ENV}-codecommit
CODECOMMIT_REPO_NAME={from stack output RepositoryName}
CODECOMMIT_CLONE_URL={from stack output CloneUrlHttp}
```

### 7.3 .env Update Strategy

1. Read the existing `.env` file.
2. Look for the `# IPA Pipeline Configuration` header line.
3. **If the block exists**: replace everything from that header through the next blank line (or end of file) with the new pipeline block.
4. **If the block does not exist**: append the pipeline block after the last line of the file (add a blank line separator first).
5. **Preserve all other content**: init, security, OIDC, ECR variables MUST remain unchanged.

---

## Step 8: Completion Report

Display:

```
Pipeline deployed successfully!

Pipeline URL:
  https://{AWS_REGION}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{PIPELINE_NAME}/view

Clone URL:
  {CODECOMMIT_CLONE_URL}

Push instructions:
  git remote add codecommit {CODECOMMIT_CLONE_URL}
  git push codecommit main

Note: The pipeline will trigger automatically on the first push.
The build executes: test → build → deploy → post-deploy
(same Make targets as local deployment)
```

Written to `.env`:
```
  PIPELINE_STACK_NAME={value}
  PIPELINE_NAME={value}
  CODEBUILD_PROJECT_NAME={value}
  CODECOMMIT_STACK_NAME={value}
  CODECOMMIT_REPO_NAME={value}
  CODECOMMIT_CLONE_URL={value}
```

---

## Re-Run / Update Flow

This flow runs when pre-flight checks detect existing pipeline configuration (Step 1.5 or 1.6).

### U1: Read Current Configuration

1. Read from `.env`: `PIPELINE_STACK_NAME`, `PIPELINE_NAME`, `CODEBUILD_PROJECT_NAME`, `CODECOMMIT_STACK_NAME`, `CODECOMMIT_REPO_NAME`, `CODECOMMIT_CLONE_URL`
2. Query the codepipeline stack:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stacks \
     --stack-name {PIPELINE_STACK_NAME} \
     --output json
   ```

### U2: Display Current Configuration

```
Current Pipeline Configuration:
┌────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Setting                │ Current Value                                               │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Pipeline Name          │ {PIPELINE_NAME}                                             │
│ CodeBuild Project      │ {CODEBUILD_PROJECT_NAME}                                    │
│ Repository Name        │ {CODECOMMIT_REPO_NAME}                                      │
│ Clone URL              │ {CODECOMMIT_CLONE_URL}                                      │
│ CodeCommit Stack       │ {CODECOMMIT_STACK_NAME}                                     │
│ CodePipeline Stack     │ {PIPELINE_STACK_NAME}                                       │
└────────────────────────┴─────────────────────────────────────────────────────────────┘
```

### U3: Update Prompt

Use AskUserQuestion:
- Question: "Would you like to update the pipeline configuration?"
- Header: "Update"
- Options:
  - **"Yes, update"** — "Re-query prepare stacks and update the pipeline"
  - **"No, keep current"** — "Keep the current configuration as-is"
- multiSelect: false

- If **"No, keep current"**: complete with "Pipeline configuration is current. No changes needed."
- If **"Yes, update"**: re-run Steps 3-8 (re-query prepare stacks, re-deploy both stacks, update `.env`).

---

## Error Handling

### ROLLBACK_COMPLETE Recovery

If either stack is in `ROLLBACK_COMPLETE` state:

1. Display: "The stack `{stack_name}` is in ROLLBACK_COMPLETE state from a previous failed deployment."
2. Use AskUserQuestion:
   - Question: "Delete the failed stack and retry?"
   - Header: "Recovery"
   - Options:
     - **"Yes, delete and retry"** — "Delete the failed stack and create a new one"
     - **"No, abort"** — "Stop here; fix manually via AWS Console or CLI"
   - multiSelect: false
3. **If "Yes, delete and retry"**:
   ```bash
   source .env 2>/dev/null; aws cloudformation delete-stack --stack-name {stack_name}
   source .env 2>/dev/null; aws cloudformation wait stack-delete-complete --stack-name {stack_name}
   ```
   Then restart from Step 5 (or Step 2 if it was the codecommit stack).
4. **If "No, abort"**: abort with "Aborting. You can manually delete the stack via AWS Console or CLI and re-run `/ipa.codepipeline`."

### Stack Creation Failure

If CloudFormation deployment fails:

1. Read stack events to identify the failure:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stack-events \
     --stack-name {stack_name} \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
     --output table
   ```
2. Diagnose using the TROUBLESHOOT.md files in the respective stack skill directories.
3. Display the failure reason and recommended recovery action.

### Stack Already Exists But Not in .env

If the CloudFormation stack exists but `.env` doesn't have `PIPELINE_STACK_NAME`:

1. Display: "Found existing pipeline stack `{stack_name}` but `.env` is missing pipeline variables."
2. Offer to import: read stack outputs and write them to `.env` (proceed to Step 7).

### Missing Prerequisites

| Missing | Error Message |
|---------|---------------|
| `.env` init vars | "Run `/ipa.init` first to configure project defaults." |
| `APP_CODEBUILD_ROLE_ARN` | "Run `/ipa.security` first to provision the CodeBuild execution role." |
| `scripts/deploy.mk` | "Run `/ipa.compose` first to generate Makefiles." |
| `buildspec.yml` | "Create `buildspec.yml` at the repository root." |
| ECR stack | "Run `/ipa.prepare` first to deploy prerequisite stacks." |
| Cognito stack | "Run `/ipa.prepare` first to deploy prerequisite stacks." |

---

## Edge Cases

- **CodeCommit repository already exists outside of IPA**: The codecommit stack creation will fail with a naming conflict. The builder should use a different repository name or import the existing repository.
- **Artifact bucket name collision**: S3 bucket names are globally unique. If `{namespace}-{env}-pipeline-artifacts-{account_id}` collides, change `APP_NAMESPACE` via `/ipa.init`.
- **Prepare stacks redeployed with different outputs**: Re-run `/ipa.codepipeline` to update the pipeline stack with new ECR and Cognito values.
- **Execution role permissions changed**: If `/ipa.security` was re-run with different permissions after pipeline creation, the pipeline may fail. The CodeBuild execution role must have permissions to deploy CloudFormation stacks.
- **Pipeline triggers on first creation**: Expected behavior. The first build will fail because no code has been pushed. Push code to start a successful build.
