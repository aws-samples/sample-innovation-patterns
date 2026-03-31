# Troubleshooting: ipa.stack.lambda

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails — PassRole error | `deploy-fn` fails with "is not authorized to perform: iam:PassRole on resource" | The Builder Execution Role lacks `iam:PassRole` permission for the Lambda execution role ARN pattern `{APP_NAMESPACE}-{APP_ENV}-*-exec`. | Add `iam:PassRole` to the Builder Execution Role with resource `arn:aws:iam::{account}:role/{APP_NAMESPACE}-{APP_ENV}-*-exec`. Re-run `/ipa.security` to regenerate the role policy. |
| 2 | Function fails to start — ECR image pull error | Function enters `Pending` state indefinitely or logs "EcrImagePullError" | The container image does not exist in ECR, or the execution role lacks `ecr:BatchGetImage` and `ecr:GetDownloadUrlForLayer` permissions. The image tag may not match what was pushed. | Verify the image exists: `aws ecr describe-images --repository-name {APP_NAMESPACE}-{APP_ENV}-ecr --image-ids imageTag=$(python3 scripts/util/version.py docker)`. If missing, run `make -f scripts/build.mk build-fn` to build and push. If the image exists, check execution role permissions. |
| 3 | Function timeout | Function invocation returns "Task timed out after N seconds" | The configured `Timeout` is too short for the workload, or `MemorySize` is too low (CPU scales with memory in Lambda). | Increase `Timeout` or `MemorySize` parameters and re-deploy. For container image cold starts, 512 MB / 30s is the minimum recommended; increase to 1024+ MB for faster cold starts. |
| 4 | Environment variable missing — wiring mismatch | Application returns auth errors (401) or database errors at runtime | `AuthIssuer`, `AuthAudience`, or `TableName` environment variables are empty or incorrect because the wiring between Cognito/DynamoDB outputs and Lambda parameters was not configured. | Verify wiring in PATTERN.md matches the stack outputs. Run `/ipa.compose` to regenerate deploy.mk. Check deployed env vars: `aws lambda get-function-configuration --function-name {APP_NAMESPACE}-{APP_ENV}-{suffix} --query 'Environment.Variables'`. |
| 5 | Stack deletion hangs | `teardown-fn` or `teardown-fn-stream` hangs at `wait stack-delete-complete` | Active Lambda invocations, event source mappings, or resource policies referencing the function prevent deletion. CloudFormation waits for the function to become idle. | Cancel active invocations. Remove event source mappings: `aws lambda list-event-source-mappings --function-name {name}`. Remove resource policies: `aws lambda get-policy --function-name {name}`. Then retry the delete. If stuck in DELETE_FAILED, delete with `aws cloudformation delete-stack` and manually clean up residual resources. |

## Additional Troubleshooting

### Image tag not found

**Symptom**: Stack creation or update fails with "Source image ... does not exist" or similar ECR error.

**Root Cause**: The container image was not built and pushed to ECR before the Lambda deploy target ran. The `IMAGE_TAG` value (resolved from `scripts/util/version.py docker`) does not match any tag in the ECR repository.

**Recovery**: Build and push the image first: `make -f scripts/build.mk build-fn`. Verify the tag exists: `aws ecr describe-images --repository-name {APP_NAMESPACE}-{APP_ENV}-ecr --image-ids imageTag=$(python3 scripts/util/version.py docker)`. Then re-deploy: `make -f scripts/deploy.mk deploy-fn`.

### DynamoDB access denied

**Symptom**: Application logs show "AccessDeniedException" when accessing DynamoDB at runtime.

**Root Cause**: The `DynamoDbTableArns` parameter value does not match the actual DynamoDB table ARN. The execution role's DynamoDB policy is scoped to the ARN(s) passed via parameter — a mismatch means no access.

**Recovery**: Verify the DynamoDB stack output: `aws cloudformation describe-stacks --stack-name {APP_NAMESPACE}-{APP_ENV}-ddb --query 'Stacks[0].Outputs[?OutputKey==\`TableArn\`].OutputValue' --output text`. Compare with the Lambda function's execution role policy. Re-run `/ipa.compose` and redeploy if the wiring is incorrect.

### Stack update fails with "No updates are to be performed"

**Symptom**: `aws cloudformation deploy` exits with an error about no updates.

**Root Cause**: The parameters and template have not changed since the last deployment.

**Recovery**: This is not an error — the stack is already in the desired state. The `aws cloudformation deploy --no-fail-on-empty-changeset` flag handles this gracefully and should not report it as a failure.
