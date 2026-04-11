# Troubleshooting: ipa.stack.codepipeline

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | CodeBuild role does not exist | Stack creation fails with "Role ARN does not exist" or "InvalidInputException" on CodeBuildProject | The `APP_CODEBUILD_ROLE_ARN` from `.env` references a role that doesn't exist or was deleted. | Run `/ipa.security` to create the CodeBuild execution role. Verify `APP_CODEBUILD_ROLE_ARN` in `.env` matches the stack output. |
| 2 | Artifact bucket naming conflict | Stack creation fails with "BucketAlreadyExists" or "BucketAlreadyOwnedByYou" | S3 bucket names are globally unique. Another account or project owns `{namespace}-{env}-pipeline-artifacts-{account_id}`. | Change `APP_NAMESPACE` via `/ipa.init` to produce a different bucket name. Or delete the existing bucket if it's unused. |
| 3 | Source repository not found | Pipeline fails on first execution with "Repository not found" in Source stage | The CodeCommit repository referenced by `SourceRepoName` does not exist, or the codecommit stack failed to deploy. | Verify the codecommit stack deployed successfully: `source .env 2>/dev/null; aws cloudformation describe-stacks --stack-name {namespace}-{env}-codecommit`. Re-run `/ipa.codepipeline` if the codecommit stack is missing. |
| 4 | Privileged mode denied | CodeBuild execution fails with Docker permission errors ("Cannot connect to the Docker daemon") | Account-level CodeBuild settings may restrict privileged mode, or the CodeBuild service role lacks required permissions. | Check AWS Organizations SCPs or CodeBuild account settings. Verify the CodeBuild execution role has the necessary permissions for Docker operations. |
| 5 | Pipeline triggers on first creation | Pipeline runs immediately after stack creation before any code is pushed | This is expected behavior — EventBridge may trigger on initial repository state. The build will fail at `pre_build` because no source code exists. | Push code to the CodeCommit repository. The next pipeline run will succeed. The initial auto-trigger failure is harmless and can be ignored. |
| 6 | IAM role creation fails | Stack creation fails with "AccessDenied" on PipelineRole or EventRuleRole | The builder's credentials lack `iam:CreateRole` or `iam:PassRole` permissions. | Verify the deployment role (from `/ipa.security`) has IAM permissions. The stack requires `CAPABILITY_NAMED_IAM`. |

## Additional Troubleshooting

### Stack update fails with "No updates are to be performed"

**Symptom**: `aws cloudformation deploy` exits with a message about no updates.

**Root Cause**: The parameters and template have not changed since the last deployment.

**Recovery**: This is not an error — the stack is already in the desired state. The `--no-fail-on-empty-changeset` flag handles this gracefully.

### CodeBuild environment variables not resolving

**Symptom**: Make targets fail because `ECR_REPO_URI`, `OIDC_ISSUER`, or other variables are empty in the CodeBuild environment.

**Root Cause**: The prepare stacks (ECR, Cognito) may have been redeployed with different outputs after the pipeline was created, but the pipeline stack was not updated with the new values.

**Recovery**: Re-run `/ipa.codepipeline` to update the pipeline stack. The process skill re-queries prepare-stack outputs and passes them as updated template parameters.

### Build fails at install phase

**Symptom**: CodeBuild fails during `pip install uv` or `uv sync`.

**Root Cause**: Network connectivity issues in CodeBuild VPC configuration, or pip/PyPI is temporarily unavailable.

**Recovery**: Retry the build. If persistent, check CodeBuild VPC settings (if configured) and ensure outbound internet access is available.

### Missing execution role — run /ipa.security

If the pipeline stack fails because the CodeBuild role doesn't exist, the issue is that `/ipa.security` was not run or its stack was deleted. Run `/ipa.security` first to create the execution roles, then re-run `/ipa.codepipeline`.
