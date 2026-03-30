# Troubleshooting: ipa.stack.ecr

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails | `deploy-ecr` fails with CREATE_FAILED or parameter validation error | Invalid Namespace (does not match AllowedPattern) or invalid Environment value. Or ECR service is not available in the target region. | Check parameter values match validation rules. Verify region supports ECR. If stack is in ROLLBACK_COMPLETE, delete it first: `aws cloudformation delete-stack --stack-name {stack-name}`, then re-deploy. |
| 2 | Docker push to ECR fails | `docker push` or `docker build` fails with authentication or authorization error | ECR login token expired (tokens last 12 hours), or the IAM principal lacks ecr:GetAuthorizationToken or ecr:PutImage permissions. | Re-authenticate: `aws ecr get-login-password --region {region} \| docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com`. Verify IAM permissions include ecr:GetAuthorizationToken (on *) and ecr:PutImage, ecr:InitiateLayerUpload, ecr:UploadLayerPart, ecr:CompleteLayerUpload (on repository ARN). |
| 3 | Stack deletion fails because repository is not empty | `cfn-delete` fails with "The repository with name '{name}' in registry with id '{account}' cannot be deleted because it still contains images" | ECR repositories cannot be deleted while they contain images (ForceDelete is not enabled — by design for safety). | Remove all images first, then delete the stack: `aws ecr list-images --repository-name {APP_NAMESPACE}-{APP_ENV}-ecr --query 'imageIds[*]' --output json` then `aws ecr batch-delete-image --repository-name {APP_NAMESPACE}-{APP_ENV}-ecr --image-ids "$(aws ecr list-images --repository-name {APP_NAMESPACE}-{APP_ENV}-ecr --query 'imageIds[*]' --output json)"` then `aws cloudformation delete-stack --stack-name {APP_NAMESPACE}-{APP_ENV}-ecr`. |

## Additional Troubleshooting

### Stack update fails with "No updates are to be performed"

**Symptom**: `aws cloudformation deploy` exits with an error about no updates.

**Root Cause**: The parameters and template have not changed since the last deployment.

**Recovery**: This is not an error — the stack is already in the desired state. The `aws cloudformation deploy --no-fail-on-empty-changeset` flag handles this gracefully and should not report it as a failure.

### Repository name already exists

**Symptom**: Stack creation fails with "Repository already exists" error.

**Root Cause**: Another stack or manual creation already created a repository with the same name in this account+region.

**Recovery**: Either delete the existing repository (if unused) or change the Namespace/Environment to produce a different repository name.
