---
name: ipa.security
description: "Provision or update centralized security infrastructure (IAM roles, log bucket) for an IPA project. Use when the user says 'security', 'set up security', 'IAM roles', or invokes /ipa.security."
model: opus
---

# /ipa.security — Provision Security Infrastructure

This skill provisions or updates centralized security infrastructure for an IPA project: IAM execution roles (Builder and CodeBuild) and a centralized S3 log bucket. It supports two configuration paths — managed policy (skill creates roles) or existing role ARNs (builder provides pre-provisioned roles). All resources are deployed as a single CloudFormation stack, and the resulting identifiers are written to `.env` for consumption by downstream IPA skills (`/ipa.compose`, `/ipa.deploy`, `/ipa.codepipeline`).

> **AWS credential resolution**: All `aws` CLI commands must be prefixed with `source .env 2>/dev/null;` to load credentials into the environment. Do NOT pass `--profile` or `--region` flags explicitly.

---

## Variable Schema

The skill manages these variables in the `.env` file's `# IPA Security Configuration` block:

| Variable | Set By | Condition | Description |
|----------|--------|-----------|-------------|
| `APP_BUILDER_ROLE_ARN` | Stack output or builder input | Always | Builder execution role ARN |
| `APP_CODEBUILD_ROLE_ARN` | Stack output or builder input | Always (managed policy) / Optional (existing role) | CodeBuild execution role ARN |
| `APP_KMS_KEY_ARN` | _(removed — no longer prompted)_ | _(legacy)_ | KMS key ARN — skill always uses SSE-S3 (AES-256); this variable is not written to `.env` |

> **Derived at runtime (not stored in `.env`)**:
> - Security stack name: `{APP_NAMESPACE}-{APP_ENV}-security` (convention)
> - Log bucket name: `{APP_NAMESPACE}-{APP_ENV}-logs-{AWS_ACCOUNT_ID}-{AWS_REGION}` (convention)
> - Managed policy: read from CloudFormation stack parameters via `describe-stacks`

### .env File Format

Security variables use standard `KEY=VALUE` format — no quotes, no `export`, no spaces around `=`. They are written as a group under the `# IPA Security Configuration` header comment, AFTER the existing `# IPA Project Configuration` block written by `/ipa.init`.

---

## Validation Rules

Validate every builder-provided value before proceeding. If validation fails, display the error message and re-prompt.

| Input | Pattern | Error Message |
|-------|---------|---------------|
| Managed policy (short name) | `/^[A-Za-z][A-Za-z0-9+=,.@_-]{0,127}$/` | "Invalid policy name — must be a valid IAM policy name" |
| Managed policy (AWS ARN) | `/^arn:aws:iam::aws:policy\/[A-Za-z0-9+=,.@_\/-]+$/` | "Invalid AWS managed policy ARN format" |
| Managed policy (custom ARN) | `/^arn:aws:iam::\d{12}:policy\/[A-Za-z0-9+=,.@_\/-]+$/` | "Invalid customer managed policy ARN format" |
| Existing role ARN | `/^arn:aws:iam::\d{12}:role\/[A-Za-z0-9+=,.@_\/-]+$/` | "Invalid role ARN — expected format: arn:aws:iam::{account}:role/{name}" |
| KMS key ARN | `/^arn:aws:kms:[a-z0-9-]+:\d{12}:key\/[a-f0-9-]+$/` | "Invalid KMS key ARN format" |

Accept all three managed policy formats:
1. **Short name**: `MyCustomPolicy` → resolve to `arn:aws:iam::aws:policy/MyCustomPolicy`
2. **AWS-managed ARN**: `arn:aws:iam::aws:policy/ReadOnlyAccess` → use as-is
3. **Customer-managed ARN**: `arn:aws:iam::123456789012:policy/CustomPolicy` → use as-is

---

## Step 1: Pre-Flight Checks

Before any prompting, verify prerequisites and determine execution flow.

### 1.1 Verify `.env` Prerequisites

Read `.env` at the project root and check for these variables (written by `/ipa.init`):
- `APP_NAMESPACE`
- `APP_ENV`
- `AWS_ACCOUNT_ID`
- `AWS_REGION`
- `AWS_PROFILE`

**If any are missing**: STOP with: "Cannot proceed — `.env` is missing required IPA variables. Run `/ipa.init` first to configure project defaults."

### 1.2 Detect Existing Security Configuration

Check if `.env` contains `APP_BUILDER_ROLE_ARN`:

- **If present** → route to the **Update Flow** (see "Re-Run / Update Flow" section).
- **If absent** → continue to step 1.3.

### 1.3 Check CloudFormation Stack Status

Compute the stack name: `{APP_NAMESPACE}-{APP_ENV}-security`

Run:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-security \
  --query 'Stacks[0].StackStatus' \
  --output text
```

- **Stack does not exist** → continue with **First-Time Flow** (Step 2).
- **Stack exists and NOT `ROLLBACK_COMPLETE`** → route to **Update Flow**.
- **Stack in `ROLLBACK_COMPLETE`** → route to **ROLLBACK_COMPLETE Recovery** (see "Error Handling" section).

---

## Step 2: Path Selection (First-Time Flow)

Use AskUserQuestion with 1 question:

**Security configuration** (header: "IAM Roles", multiSelect: false)
- Question: "How should IPA configure IAM execution roles?"
- Options:
  - **"Managed policy" (Recommended)** — "IPA creates Builder and CodeBuild roles; you provide the policy name"
  - **"Existing role ARNs"** — "Skip role creation; provide pre-provisioned role ARNs"
- The path selection must NOT name specific policies — policy choices are deferred to Step 3a.

- If the builder selects **"Managed policy"** → proceed to **Step 3a: Managed Policy Input**.
- If the builder selects **"Existing role ARNs"** → proceed to **Step 3b: Existing Role ARN Input**.

---

## Step 3a: Managed Policy Input

1. Use AskUserQuestion:
   - Question: "Which managed policy should IPA attach to both execution roles?"
   - Header: "Policy"
   - Options:
     - **"PowerUserAccess (Recommended)"** — "Broad AWS access without IAM administration"
     - **"ReadOnlyAccess"** — "Read-only access across AWS services"
   - multiSelect: false
   The builder may select a predefined option or use "Other" to type a custom policy name or full ARN (e.g., `MyCustomPolicy` or `arn:aws:iam::123456789012:policy/MyPolicy`).
2. Validate the input against the three accepted formats (see Validation Rules).
3. If it's a short name (no `arn:` prefix): resolve to `arn:aws:iam::aws:policy/{name}`.
4. Store the resolved ARN as `ManagedPolicyArn` for template generation.
5. Proceed to **Step 5: Confirmation Summary**.

---

## Step 3b: Existing Role ARN Input

### 3b.1 Builder Execution Role (Required)

1. Prompt: "Enter the Builder execution role ARN:"
2. Validate ARN format (see Validation Rules).
3. Verify the role exists:
   ```bash
   source .env 2>/dev/null; aws iam get-role \
     --role-name {role_name_extracted_from_arn}
   ```
4. If the role is not found: display "Role not found: `{arn}`. Check the ARN and try again." and re-prompt.

### 3b.2 CodeBuild Execution Role (Optional)

1. Prompt: "Enter the CodeBuild execution role ARN, or press Enter to skip (can be provided later via `/ipa.codepipeline`):"
2. If provided:
   - Validate ARN format.
   - Verify the role exists (same `aws iam get-role` check).
   - If not found: display error and re-prompt.
3. If skipped (empty input): note that `APP_CODEBUILD_ROLE_ARN` will be omitted from `.env`.

### 3b.3 Permissions Warning

After role validation, display:

> **Note**: IPA cannot validate that these roles have sufficient permissions for your composed pattern. If deployments fail with permission errors, re-run `/ipa.security` with a managed policy instead.

4. Proceed to **Step 5: Confirmation Summary**.

---

## Step 5: Confirmation Summary

> **Note**: KMS encryption is not prompted. The log bucket always uses SSE-S3 (AES-256) encryption. The CloudFormation template retains the `KmsKeyArn` parameter with its default empty string for backwards compatibility — always pass `KmsKeyArn=""` during deployment.

Display a confirmation table before deployment. Adapt the content based on the chosen path.

### Managed Policy Path Example:

```
┌──────────────────────┬─────────────────────────────────────────────────┬───────────────┐
│ Setting              │ Value                                           │ Source        │
├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤
│ Path                 │ Managed Policy                                  │ prompted      │
│ Managed Policy       │ {builder's policy}                              │ prompted      │
│ Builder Role         │ (will be created)                               │ generated     │
│ CodeBuild Role       │ (will be created)                               │ generated     │
│ Security Stack       │ myproject-dev-security                          │ computed      │
│ Log Bucket           │ myproject-dev-logs-123456789012-us-east-1       │ computed      │
│ Encryption           │ SSE-S3 (AES-256)                                │ default       │
└──────────────────────┴─────────────────────────────────────────────────┴───────────────┘
```

### Existing Role ARN Path Example:

```
┌──────────────────────┬─────────────────────────────────────────────────┬───────────────┐
│ Setting              │ Value                                           │ Source        │
├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤
│ Path                 │ Existing Role ARNs                              │ prompted      │
│ Builder Role ARN     │ arn:aws:iam::123456789012:role/my-builder       │ prompted      │
│ CodeBuild Role ARN   │ (skipped — deferred to /ipa.codepipeline)      │ skipped       │
│ Security Stack       │ myproject-dev-security                          │ computed      │
│ Log Bucket           │ myproject-dev-logs-123456789012-us-east-1       │ computed      │
│ Encryption           │ SSE-S3 (AES-256)                                │ default       │
└──────────────────────┴─────────────────────────────────────────────────┴───────────────┘
```

Use AskUserQuestion:
- Question: "Deploy this security configuration?"
- Header: "Deploy"
- Options:
  - **"Yes, deploy"** — "Deploy the security stack with the configuration shown above"
  - **"No, start over"** — "Return to path selection and re-enter configuration"
- multiSelect: false

- If **"Yes, deploy"** → proceed to **Step 6: Generate and Deploy**.
- If **"No, start over"** → restart from Step 2.

---

## Step 6: Generate CloudFormation Template

Create the directory if it does not exist:
```bash
mkdir -p infra/cfn/generated
```

Write the template to `infra/cfn/generated/security.yml` based on the chosen path.

### 6a: Managed Policy Path Template

Write this YAML to `infra/cfn/generated/security.yml`, substituting `{variables}` with actual values:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: "IPA Security Stack — IAM execution roles and centralized log bucket"

Parameters:
  Namespace:
    Type: String
  Environment:
    Type: String
  AccountId:
    Type: String
  Region:
    Type: String
  ManagedPolicyArn:
    Type: String
  KmsKeyArn:
    Type: String
    Default: ""

Conditions:
  UseKmsKey: !Not [!Equals [!Ref KmsKeyArn, ""]]

Resources:
  BuilderExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "${Namespace}-${Environment}-builder"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub "arn:aws:iam::${AccountId}:root"
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - !Ref ManagedPolicyArn

  CodeBuildExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "${Namespace}-${Environment}-codebuild"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - !Ref ManagedPolicyArn

  LogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${Namespace}-${Environment}-logs-${AccountId}-${Region}"
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: !If [UseKmsKey, "aws:kms", "AES256"]
              KMSMasterKeyID: !If [UseKmsKey, !Ref KmsKeyArn, !Ref "AWS::NoValue"]
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: ExpireLogs
            Status: Enabled
            ExpirationInDays: 90

  LogBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref LogBucket
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Sid: AllowS3ServerAccessLogs
            Effect: Allow
            Principal:
              Service: logging.s3.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/s3-access-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: AllowCloudFrontLogs
            Effect: Allow
            Principal:
              Service: cloudfront.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/cloudfront-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: AllowVPCFlowLogs
            Effect: Allow
            Principal:
              Service: delivery.logs.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/vpc-flow-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: DenyNonSSL
            Effect: Deny
            Principal: "*"
            Action: "s3:*"
            Resource:
              - !Sub "arn:aws:s3:::${LogBucket}"
              - !Sub "arn:aws:s3:::${LogBucket}/*"
            Condition:
              Bool:
                "aws:SecureTransport": "false"

Outputs:
  BuilderRoleArn:
    Value: !GetAtt BuilderExecutionRole.Arn
    Export:
      Name: !Sub "${AWS::StackName}-BuilderRoleArn"
  CodeBuildRoleArn:
    Value: !GetAtt CodeBuildExecutionRole.Arn
    Export:
      Name: !Sub "${AWS::StackName}-CodeBuildRoleArn"
  LogBucketName:
    Value: !Ref LogBucket
    Export:
      Name: !Sub "${AWS::StackName}-LogBucketName"
  LogBucketArn:
    Value: !GetAtt LogBucket.Arn
    Export:
      Name: !Sub "${AWS::StackName}-LogBucketArn"
```

### 6b: Existing Role ARN Path Template

Write this YAML to `infra/cfn/generated/security.yml` — same log bucket resources, NO IAM roles:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: "IPA Security Stack — centralized log bucket (existing IAM roles)"

Parameters:
  Namespace:
    Type: String
  Environment:
    Type: String
  AccountId:
    Type: String
  Region:
    Type: String
  KmsKeyArn:
    Type: String
    Default: ""

Conditions:
  UseKmsKey: !Not [!Equals [!Ref KmsKeyArn, ""]]

Resources:
  LogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${Namespace}-${Environment}-logs-${AccountId}-${Region}"
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: !If [UseKmsKey, "aws:kms", "AES256"]
              KMSMasterKeyID: !If [UseKmsKey, !Ref KmsKeyArn, !Ref "AWS::NoValue"]
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: ExpireLogs
            Status: Enabled
            ExpirationInDays: 90

  LogBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref LogBucket
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Sid: AllowS3ServerAccessLogs
            Effect: Allow
            Principal:
              Service: logging.s3.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/s3-access-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: AllowCloudFrontLogs
            Effect: Allow
            Principal:
              Service: cloudfront.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/cloudfront-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: AllowVPCFlowLogs
            Effect: Allow
            Principal:
              Service: delivery.logs.amazonaws.com
            Action: "s3:PutObject"
            Resource: !Sub "arn:aws:s3:::${LogBucket}/vpc-flow-logs/*"
            Condition:
              StringEquals:
                "aws:SourceAccount": !Ref AccountId
          - Sid: DenyNonSSL
            Effect: Deny
            Principal: "*"
            Action: "s3:*"
            Resource:
              - !Sub "arn:aws:s3:::${LogBucket}"
              - !Sub "arn:aws:s3:::${LogBucket}/*"
            Condition:
              Bool:
                "aws:SecureTransport": "false"

Outputs:
  LogBucketName:
    Value: !Ref LogBucket
    Export:
      Name: !Sub "${AWS::StackName}-LogBucketName"
  LogBucketArn:
    Value: !GetAtt LogBucket.Arn
    Export:
      Name: !Sub "${AWS::StackName}-LogBucketArn"
```

---

## Step 7: Deploy Security Stack

### 7.1 Deployment Command

Deploy using AWS CLI:

```bash
source .env 2>/dev/null; aws cloudformation deploy \
  --template-file infra/cfn/generated/security.yml \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-security \
  --parameter-overrides \
    Namespace={APP_NAMESPACE} \
    Environment={APP_ENV} \
    AccountId={AWS_ACCOUNT_ID} \
    Region={AWS_REGION} \
    ManagedPolicyArn={resolved_arn} \
    KmsKeyArn="" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

**For the existing-role-ARN path**: omit the `ManagedPolicyArn` parameter override (it is not in the template).

### 7.2 Wait for Deployment

Monitor the deployment. If it fails, proceed to the **Error Handling** section to diagnose the issue.

If deployment succeeds, proceed to **Step 8: Write .env**.

---

## Step 8: Write .env Security Variables

### 8.1 Retrieve Stack Outputs (Managed Policy Path)

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {APP_NAMESPACE}-{APP_ENV}-security \
  --query 'Stacks[0].Outputs' \
  --output json
```

Extract:
- `BuilderRoleArn` → `APP_BUILDER_ROLE_ARN`
- `CodeBuildRoleArn` → `APP_CODEBUILD_ROLE_ARN`

### 8.2 Compose .env Security Block

#### Managed Policy Path:

```
# IPA Security Configuration
# Generated by /ipa.security — local only, do not commit
APP_BUILDER_ROLE_ARN={from stack output BuilderRoleArn}
APP_CODEBUILD_ROLE_ARN={from stack output CodeBuildRoleArn}
```

#### Existing Role ARN Path:

```
# IPA Security Configuration
# Generated by /ipa.security — local only, do not commit
APP_BUILDER_ROLE_ARN={builder-provided ARN}
```

Include `APP_CODEBUILD_ROLE_ARN={builder-provided ARN}` only if the builder provided a CodeBuild role ARN (not skipped).

### 8.3 .env Update Strategy

1. Read the existing `.env` file.
2. Look for the `# IPA Security Configuration` header line.
3. **If the block exists**: replace everything from that header through the next blank line (or end of file) with the new security block.
4. **If the block does not exist**: append the security block after the last line of the file (add a blank line separator first).
5. **Preserve all other content**: init variables (`# IPA Project Configuration` block), non-IPA variables, comments, and blank lines MUST remain unchanged in their original positions.

### 8.4 Completion Message

Display: "Security stack deployed successfully. `.env` updated with security variables."

Show a summary of written values:
```
Written to .env:
  APP_BUILDER_ROLE_ARN={value}
  APP_CODEBUILD_ROLE_ARN={value}

Next steps:
  • Run `/ipa.compose` to compose infrastructure and generate Makefiles
  • Run `/ipa.security` again to review or update the configuration
  • Re-run `/ipa.init` to change project namespace or environment
```

---

## Re-Run / Update Flow

This flow runs when pre-flight checks detect existing security configuration (Step 1.2 or 1.3).

### U1: Read Current Configuration

1. Read from `.env`: `APP_BUILDER_ROLE_ARN`, `APP_CODEBUILD_ROLE_ARN` (may be absent)
2. Compute security stack name: `{APP_NAMESPACE}-{APP_ENV}-security`
3. Query the stack:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stacks \
     --stack-name {APP_NAMESPACE}-{APP_ENV}-security \
     --output json
   ```
4. Extract from the response:
   - `Stacks[0].StackStatus` — verify it's a `*_COMPLETE` state (not `ROLLBACK_COMPLETE`)
   - `Stacks[0].Parameters` — find `ManagedPolicyArn` (if present → managed policy path)
   - `Stacks[0].Outputs` — find `LogBucketName` (for display)

### U2: Display Current Configuration

**Infrastructure context (optional):**

Run:
```bash
source .env 2>/dev/null; aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?starts_with(StackName, '{APP_NAMESPACE}-{APP_ENV}')].{Name:StackName,Status:StackStatus,Updated:LastUpdatedTime}" \
  --output table
```

If successful, display the output prefixed with:
```
Current Infrastructure ({APP_NAMESPACE}-{APP_ENV}):
{list-stacks output}
```

If the command fails, skip silently.

**Security configuration table:**

Display the configuration table using values from `.env` reads (role ARNs, KMS) and CloudFormation queries (path, managed policy, log bucket, stack name):

```
Current Security Configuration:
┌──────────────────────┬─────────────────────────────────────────────────┐
│ Setting              │ Current Value                                   │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Path                 │ {from stack resources}                          │
│ Managed Policy       │ {from stack parameter ManagedPolicyArn}         │
│ Builder Role ARN     │ {from .env APP_BUILDER_ROLE_ARN}               │
│ CodeBuild Role ARN   │ {from .env APP_CODEBUILD_ROLE_ARN}             │
│ Security Stack       │ {APP_NAMESPACE}-{APP_ENV}-security (computed)   │
│ Log Bucket           │ {from stack output or computed}                 │
│ Encryption           │ SSE-S3 (AES-256)                                │
└──────────────────────┴─────────────────────────────────────────────────┘
```

Infer the current path from the stack's `describe-stacks` response: if `ManagedPolicyArn` is present in `Stacks[0].Parameters` → "Managed Policy"; otherwise → "Existing Role ARNs".

### U3: Update Prompt

Use AskUserQuestion:
- Question: "Would you like to update the security configuration?"
- Header: "Update"
- Options:
  - **"Yes, update"** — "Modify the security configuration"
  - **"No, keep current"** — "Keep the current configuration as-is"
- multiSelect: false

- If **"No, keep current"**: complete with "Security configuration is current. No changes needed."
- If **"Yes, update"**: proceed to Step 2 (Path Selection) to re-enter the full configuration flow.

### U4: Path Switching Warning

If the builder is switching paths:

- **Managed → Existing**: Use AskUserQuestion:
  - Question: "Switching to existing role ARNs will REMOVE the IAM roles currently managed by the security stack. The stack will be updated to contain only the log bucket. Proceed?"
  - Header: "Confirm"
  - Options:
    - **"Yes, switch paths"** — "Remove managed roles and use existing role ARNs"
    - **"No, keep current path"** — "Stay with managed policy configuration"
  - multiSelect: false
- **Existing → Managed**: "Note: Switching to managed policy will create new IAM roles in the security stack."

### U5: No-Change Detection

If CloudFormation returns "No updates are to be performed" during stack update:
- Treat as success.
- Display: "Security stack is up to date. No changes deployed."
- Still refresh `.env` from current stack outputs (in case `.env` was manually edited).

---

## Error Handling

### ROLLBACK_COMPLETE Recovery

If the security stack is in `ROLLBACK_COMPLETE` state:

1. Display: "The security stack `{stack_name}` is in ROLLBACK_COMPLETE state from a previous failed deployment."
2. Use AskUserQuestion:
   - Question: "Delete the failed stack and retry?"
   - Header: "Recovery"
   - Options:
     - **"Yes, delete and retry"** — "Delete the failed stack and create a new one"
     - **"No, abort"** — "Stop here; fix manually via AWS Console or CLI"
   - multiSelect: false
3. **If "Yes, delete and retry"**:
   ```bash
   source .env 2>/dev/null; aws cloudformation delete-stack \
     --stack-name {stack_name}
   ```
   Wait for deletion to complete:
   ```bash
   source .env 2>/dev/null; aws cloudformation wait stack-delete-complete \
     --stack-name {stack_name}
   ```
   Then proceed with the First-Time Flow (Step 2).
4. **If "No, abort"**: abort with "Aborting. You can manually delete the stack via AWS Console or CLI and re-run `/ipa.security`."

### Permission Errors

If CloudFormation deployment fails with an IAM permission error:

1. Read stack events to identify the failure:
   ```bash
   source .env 2>/dev/null; aws cloudformation describe-stack-events \
     --stack-name {stack_name} \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
     --output table
   ```
2. Display: "Deployment failed due to insufficient IAM permissions: {error}. Your current AWS credentials need `iam:CreateRole` and `s3:CreateBucket` permissions. Options: (a) use the existing-role-ARN path instead, (b) obtain the required permissions and retry."

### Bucket Already Exists

If CloudFormation fails with `BucketAlreadyExists`:

Display: "The log bucket name `{bucket_name}` already exists in S3 (bucket names are globally unique). This usually means another project or account owns this name. Consider changing your `APP_NAMESPACE` via `/ipa.init` to generate a different bucket name."

### Invalid Managed Policy

If CloudFormation fails because the managed policy does not exist:

1. Read stack events, identify the `AWS::IAM::Role` failure.
2. Display: "The managed policy `{policy}` was not found. Check the policy name/ARN and try again."
3. Re-prompt for the managed policy (return to Step 3a).

### Missing Prerequisites

If `.env` does not exist or does not contain IPA init variables:

STOP with: "Cannot proceed — `.env` is missing or does not contain IPA project configuration. Run `/ipa.init` first."

---

## Edge Cases

- **CloudFormation stack exists but `.env` security block is missing**: Treat as an update scenario. Read stack outputs and re-populate `.env`.
- **`.env` has security variables but stack doesn't exist**: Warn the builder that the stack may have been manually deleted. Offer to re-deploy or clear `.env` security variables.
- **Builder provides the same configuration on re-run**: CloudFormation returns "No updates are to be performed" — handle as success per U5.
- **`aws cloudformation list-stacks` fails**: Skip the infrastructure context display and proceed with the security-specific update flow using targeted `describe-stacks` calls. The infrastructure listing is informational, not blocking.
