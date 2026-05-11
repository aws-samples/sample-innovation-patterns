# Troubleshooting: ipa-stack-codecommit

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Repository already exists | Stack creation fails with "Repository named '{name}' already exists" | Another stack or manual creation already created a repository with the same name in this account+region. | Either delete the existing repository (if unused): `source .env 2>/dev/null; aws codecommit delete-repository --repository-name {name}`, or change the repository name when re-running `/ipa-codepipeline`. |
| 2 | KMS key permissions | Stack creation fails with "Access denied" or KMS-related error on the Repository resource | The builder's credentials or the deployment role lacks `kms:DescribeKey` or `kms:CreateGrant` on the provided KMS key. | Verify KMS key policy grants the deployment role access. Or remove the `KmsKeyArn` parameter to use default encryption. |
| 3 | Repository not empty on delete | Stack deletion fails with "Repository cannot be deleted because it contains branches" | CodeCommit does not allow deleting repositories that contain data unless explicitly handled. | Delete all branches first: `source .env 2>/dev/null; aws codecommit delete-repository --repository-name {name}`. Then delete the stack: `source .env 2>/dev/null; aws cloudformation delete-stack --stack-name {stack-name}`. |
| 4 | Invalid repository name | Stack creation fails with parameter validation error | Repository name contains characters not matching `[a-zA-Z0-9._-]+`. | Use only alphanumeric characters, dots, underscores, and hyphens in the repository name. |

## Additional Troubleshooting

### Stack update fails with "No updates are to be performed"

**Symptom**: `aws cloudformation deploy` exits with a message about no updates.

**Root Cause**: The parameters and template have not changed since the last deployment.

**Recovery**: This is not an error — the stack is already in the desired state. The `--no-fail-on-empty-changeset` flag handles this gracefully.

### Repository created outside of IPA

**Symptom**: `/ipa-codepipeline` attempts to create a codecommit stack, but a repository with the same name already exists (created manually or by another tool).

**Recovery**: Either import the existing repository by using a different stack name, or use a unique repository name. The process skill will detect the naming conflict and report it.
