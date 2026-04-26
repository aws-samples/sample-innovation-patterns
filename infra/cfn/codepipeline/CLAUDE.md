# infra/cfn/codepipeline/

CI/CD pipeline template for IPA automated build/test/deploy. Deployed by `/ipa.codepipeline` process skill.

## Resources

| Resource | Type | Description |
|----------|------|-------------|
| ArtifactBucket | `AWS::S3::Bucket` | Pipeline artifact storage (public access blocked, SSL enforced) |
| ArtifactBucketPolicy | `AWS::S3::BucketPolicy` | Denies non-SSL requests |
| CodeBuildProject | `AWS::CodeBuild::Project` | Build project with 9 environment variables, inline parametric buildspec, privileged mode |
| Pipeline | `AWS::CodePipeline::Pipeline` | Source → Test → Build → Deploy → PostDeploy (all stages use same CodeBuild project with different env var overrides) |
| EventRule | `AWS::Events::Rule` | Triggers pipeline on CodeCommit push (replaces polling) |
| EventRuleRole | `AWS::IAM::Role` | EventBridge role to start pipeline execution |
| PipelineRole | `AWS::IAM::Role` | Pipeline orchestration role scoped to specific resources |

## Parameters

| Parameter | Required | Default | Source |
|-----------|----------|---------|--------|
| Namespace | Yes | — | `.env` `APP_NAMESPACE` |
| Environment | Yes | — | `.env` `APP_ENV` |
| AccountId | Yes | — | `.env` `AWS_ACCOUNT_ID` |
| CodeBuildRoleArn | Yes | — | `.env` `APP_CODEBUILD_ROLE_ARN` |
| SourceRepoName | Yes | — | Builder input |
| SourceBranch | No | `main` | Builder input |
| EcrRepoUri | Yes | — | ECR stack output `RepositoryUri` |
| OidcIssuer | Yes | — | Cognito stack output `IssuerUrl` |
| OidcClientId | Yes | — | Cognito stack output `UserPoolClientId` |
| OidcEndSessionEndpoint | Yes | — | Cognito stack output `EndSessionEndpoint` |
| BuildImage | No | `aws/codebuild/standard:7.0` | Default |
| ComputeType | No | `BUILD_GENERAL1_LARGE` | Default |
| KmsKeyArn | No | *(empty)* | Optional KMS key ARN |

## CodeBuild Environment Variables

Set on the CodeBuild project, inherited by Make targets:

`APP_NAMESPACE`, `APP_ENV`, `AWS_ACCOUNT_ID`, `ECR_REPO_URI`, `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_END_SESSION_ENDPOINT`, `IPA_MAKEFILE`, `IPA_TARGET`

The `IPA_MAKEFILE` and `IPA_TARGET` variables are overridden per pipeline stage action to select which Make target to run (e.g., `test.mk`/`test`, `build.mk`/`build`, `deploy.mk`/`deploy`, `post-deploy.mk`/`post-deploy`). The buildspec is inline in the template — no external `buildspec.yml` file needed.

## PipelineRole Permissions (Scoped)

- `codebuild:StartBuild`, `codebuild:BatchGetBuilds` → CodeBuild project ARN
- `s3:GetObject`, `s3:PutObject`, `s3:GetBucketVersioning` → Artifacts bucket
- `codecommit:GetBranch`, `codecommit:GetCommit`, `codecommit:UploadArchive`, `codecommit:GetUploadArchiveStatus`, `codecommit:CancelUploadArchive` → CodeCommit repo ARN
- Conditional `kms:Decrypt`, `kms:GenerateDataKey` → KMS key ARN (when HasKmsKey)

## Security Controls

- No wildcard IAM resource ARNs — all actions scoped to specific resources
- Artifact bucket: all four PublicAccessBlock flags, deny non-SSL bucket policy
- SSE-S3 default encryption + optional KMS
- CodeBuild uses external execution role (from `/ipa.security`)
- Privileged mode always enabled (required for Docker builds)
- EventBridge trigger replaces polling (PollForSourceChanges: false)

## Capabilities

`CAPABILITY_NAMED_IAM` (creates PipelineRole and EventRuleRole)

## Stack Naming

`{APP_NAMESPACE}-{APP_ENV}-codepipeline`

## Related

- Stack skill: `.claude/skills/ipa.stack.codepipeline/`
- Process skill: `.claude/skills/ipa.codepipeline/`
- Depends on: `infra/cfn/codecommit/codecommit.yml` (Source stage), `/ipa.security` (CodeBuild role)
