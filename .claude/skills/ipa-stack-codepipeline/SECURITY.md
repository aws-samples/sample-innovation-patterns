# Security Advisory: ipa-stack-codepipeline

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the CodePipeline stack.

```yaml
permissions:
  - actions:
      - codepipeline:CreatePipeline
      - codepipeline:UpdatePipeline
      - codepipeline:DeletePipeline
      - codepipeline:GetPipeline
      - codepipeline:GetPipelineState
      - codepipeline:TagResource
      - codepipeline:UntagResource
    resource: "arn:aws:codepipeline:{AWS_REGION}:{AWS_ACCOUNT_ID}:{APP_NAMESPACE}-{APP_ENV}-pipeline"
    purpose: "CloudFormation CRUD operations on CodePipeline resource"

  - actions:
      - codebuild:CreateProject
      - codebuild:UpdateProject
      - codebuild:DeleteProject
      - codebuild:BatchGetProjects
    resource: "arn:aws:codebuild:{AWS_REGION}:{AWS_ACCOUNT_ID}:project/{APP_NAMESPACE}-{APP_ENV}-build"
    purpose: "CloudFormation CRUD operations on CodeBuild project"

  - actions:
      - s3:CreateBucket
      - s3:DeleteBucket
      - s3:PutBucketPolicy
      - s3:DeleteBucketPolicy
      - s3:PutEncryptionConfiguration
      - s3:PutBucketPublicAccessBlock
      - s3:PutBucketTagging
    resource: "arn:aws:s3:::{APP_NAMESPACE}-{APP_ENV}-pipeline-artifacts-{AWS_ACCOUNT_ID}"
    purpose: "CloudFormation CRUD operations on artifacts S3 bucket"

  - actions:
      - iam:CreateRole
      - iam:DeleteRole
      - iam:PutRolePolicy
      - iam:DeleteRolePolicy
      - iam:GetRole
      - iam:PassRole
      - iam:TagRole
      - iam:UntagRole
    resource:
      - "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{APP_NAMESPACE}-{APP_ENV}-pipeline-role"
      - "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{APP_NAMESPACE}-{APP_ENV}-pipeline-event-role"
    purpose: "CloudFormation CRUD operations on PipelineRole and EventRuleRole IAM roles"

  - actions:
      - events:PutRule
      - events:DeleteRule
      - events:PutTargets
      - events:RemoveTargets
      - events:DescribeRule
    resource: "arn:aws:events:{AWS_REGION}:{AWS_ACCOUNT_ID}:rule/*"
    purpose: "CloudFormation CRUD operations on EventBridge rule for pipeline trigger"

  - actions:
      - kms:DescribeKey
      - kms:CreateGrant
    resource: "{KmsKeyArn}"
    condition: "Only when KmsKeyArn parameter is provided (HasKmsKey condition)"
    purpose: "KMS key access for encryption at rest on artifacts bucket and CodeBuild project"
```

## Security Controls

Controls enforced by the CloudFormation template.

```yaml
controls:
  - type: iam_scoping
    enabled: true
    method: "PipelineRole is scoped to specific resources — CodeBuild project ARN, artifacts bucket ARN, CodeCommit repo ARN. No wildcard resource ARNs."

  - type: s3_public_access
    enabled: true
    method: "Artifact bucket has all four PublicAccessBlock flags enabled (BlockPublicAcls, BlockPublicPolicy, IgnorePublicAcls, RestrictPublicBuckets)"

  - type: s3_ssl_enforcement
    enabled: true
    method: "Bucket policy denies all s3:* actions when aws:SecureTransport is false"

  - type: encryption
    enabled: true
    method: "SSE-S3 (AES-256) by default. Optional KMS encryption on artifacts bucket, CodeBuild project via HasKmsKey condition"

  - type: codebuild_role_separation
    enabled: true
    method: "CodeBuild uses an external execution role (CodeBuildRoleArn from /ipa-security). The template does not create CodeBuild permissions — only pipeline orchestration permissions"

  - type: privileged_mode
    enabled: true
    method: "Always enabled on CodeBuild project for Docker-in-Docker builds. CodeBuild runs in an isolated sandbox"

  - type: event_trigger
    enabled: true
    method: "EventBridge rule replaces polling (PollForSourceChanges: false). EventRuleRole is scoped to codepipeline:StartPipelineExecution on the specific pipeline ARN"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No SNS failure notifications | POC scope — deferred | Low — builder monitors via console |
| No CloudWatch alarms | POC scope — deferred | Low — CodeBuild logs available in console |
| No cross-account pipeline | Single-account POC | Low — can be added via additional IAM trust |
