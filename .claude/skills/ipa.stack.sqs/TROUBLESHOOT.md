# Troubleshooting: ipa.stack.sqs

## Scenario 1: Stack Creation Fails — Parameter Validation

**Symptom**: `CREATE_FAILED` with status reason mentioning `AllowedPattern` or `ConstraintDescription`.

**Cause**: One of the parameters (Namespace, Environment, or QueueName) does not match its validation pattern.

**Fix**:
1. Check the error message — it identifies which parameter failed.
2. Verify `.env` values match the required patterns:
   - Namespace: 1-12 chars, lowercase letters/digits/hyphens, starts with letter
   - Environment: 1-12 chars, lowercase letters/digits/hyphens, starts with letter
   - QueueName: 1-30 chars, lowercase letters/digits/hyphens, starts with letter
3. Fix the value in `.env` and re-run `/ipa.deploy`.

## Scenario 2: Queue Already Exists — Name Collision

**Symptom**: `CREATE_FAILED` with status reason `Queue already exists`.

**Cause**: An SQS queue with the name `{Namespace}-{Environment}-{QueueName}` already exists outside of CloudFormation management.

**Fix**:
1. If the existing queue is not needed: delete it manually via `aws sqs delete-queue --queue-url {queue_url}`.
2. If the existing queue must be kept: change `QueueName` to a unique name.
3. If the queue was created by a previous stack in `ROLLBACK_COMPLETE`: delete the failed stack first, wait for deletion, then re-deploy.
4. Re-run `/ipa.deploy`.

## Scenario 3: DLQ Creation Fails — Circular Dependency

**Symptom**: `CREATE_FAILED` on the DLQ or main queue resource.

**Cause**: CloudFormation is unable to resolve the DLQ ARN reference before creating the main queue's redrive policy. This should not occur with the current template design (DLQ is created first as a separate resource), but can happen if the template is modified.

**Fix**:
1. Verify the template has not been manually modified.
2. If modified, restore from the original template in `infra/cfn/sqs/sqs.yml`.
3. If the issue persists, set `CreateDLQ=false` as a workaround, deploy, then re-enable.

## Scenario 4: Visibility Timeout Too Low

**Symptom**: Messages are re-delivered while the Lambda worker is still processing them, causing duplicate processing.

**Cause**: The SQS `VisibilityTimeout` is less than the Lambda function's `Timeout`. When the visibility window expires before Lambda finishes, SQS delivers the message again.

**Fix**:
1. Set `VisibilityTimeout` to at least 3x the Lambda `Timeout` (default: Lambda=300s, SQS=900s).
2. Update the parameter in the compose configuration and re-deploy.

## Scenario 5: "No Updates Are to Be Performed"

**Symptom**: Deploy succeeds but outputs message `No updates are to be performed`.

**Cause**: No parameter values have changed since the last deployment. CloudFormation detects no diff.

**Fix**: This is expected behavior, not an error. The `--no-fail-on-empty-changeset` flag ensures the deploy command exits 0. No action needed.
