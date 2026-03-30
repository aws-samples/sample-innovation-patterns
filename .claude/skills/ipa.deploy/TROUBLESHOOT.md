# Deploy Troubleshooting Guide

Reference file for `/ipa.deploy` — failure catalog for deploy-level issues not covered by CloudFormation event diagnosis. For CloudFormation-specific errors, see [DIAGNOSIS.md](DIAGNOSIS.md).

---

## Make Execution Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `make: command not found` | GNU Make is not installed | macOS: pre-installed. Linux: `sudo apt install make` |
| `aws: command not found` | AWS CLI is not installed | Install per https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
| `make: *** No rule to make target 'deploy'` | `scripts/deploy.mk` is missing or malformed | Run `/ipa.compose` to regenerate deployment artifacts |
| `make: *** No rule to make target 'build'` | `scripts/build.mk` is missing or malformed | Run `/ipa.compose` to regenerate build artifacts |
| `-include .env: No such file or directory` | This is a warning, not an error — `-include` silently skips missing files | If `.env` is truly missing, run `/ipa.init`. Otherwise ignore this warning. |
| `make: *** [deploy-{suffix}] Error 1` | The AWS CLI command within the target failed | Read the output above this line for the specific error. If it's a CloudFormation error, use [DIAGNOSIS.md](DIAGNOSIS.md) |

---

## Credential Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ExpiredTokenException` or `ExpiredToken` | AWS session token has expired | Refresh credentials: re-authenticate with your AWS profile (`aws sso login --profile {AWS_PROFILE}` or equivalent) |
| `InvalidClientTokenId` | AWS access key is invalid or deactivated | Verify `AWS_PROFILE` in `.env` points to a valid, active profile: `aws configure list --profile {AWS_PROFILE}` |
| `NoCredentialProviders` or `Unable to locate credentials` | No credentials configured for the profile | Configure credentials for `{AWS_PROFILE}`: `aws configure --profile {AWS_PROFILE}` or set up SSO |
| `Access Denied` on `sts:GetCallerIdentity` | Profile exists but cannot authenticate | Check that the profile's credentials are current and the IAM user/role is active |
| `SignatureDoesNotMatch` | Clock skew or corrupted credentials | Sync system clock (`sudo ntpdate pool.ntp.org`), then retry. If persists, reconfigure credentials |

---

## Generic CloudFormation Errors

| Error / State | Cause | Fix |
|---------------|-------|-----|
| `ROLLBACK_COMPLETE` | Stack creation failed and rolled back | **Auto-recovery available**: `/ipa.deploy` can delete the stack and retry. Or manually: `aws cloudformation delete-stack --stack-name {stack}` then `aws cloudformation wait stack-delete-complete --stack-name {stack}`, then re-run `/ipa.deploy` |
| `CREATE_FAILED` | A resource within the stack failed to create | Run `aws cloudformation describe-stack-events --stack-name {stack}` to see which resource failed and why. Classify per [DIAGNOSIS.md](DIAGNOSIS.md) |
| `UPDATE_ROLLBACK_COMPLETE` | Stack update failed and rolled back to previous state | The stack is in a stable state with the previous configuration. Fix the root cause (check `cfn-events`), then re-run `/ipa.deploy` to retry the update |
| `DELETE_FAILED` | Stack deletion failed (usually during teardown) | Check `cfn-events` for the blocking resource. Common cause: non-empty S3 buckets or ECR repositories. Empty the resource, then retry teardown |
| Timeout (60 minutes) | Stack operation exceeded the wait timeout | The stack may still be in progress. Check status: `aws cloudformation describe-stacks --stack-name {stack} --query 'Stacks[0].StackStatus' --output text`. Wait for it to reach a terminal state, then re-run `/ipa.deploy` |

