# Troubleshooting: ipa.stack.dynamodb

## Scenario 1: Stack Creation Fails — Parameter Validation

**Symptom**: `CREATE_FAILED` with status reason mentioning `AllowedPattern` or `ConstraintDescription`.

**Cause**: One of the parameters (Namespace, Environment, or TableName) does not match its validation pattern.

**Fix**:
1. Check the error message — it identifies which parameter failed.
2. Verify `.env` values match the required patterns:
   - Namespace: 1-12 chars, lowercase letters/digits/hyphens, starts with letter
   - Environment: 1-12 chars, lowercase letters/digits/hyphens, starts with letter
   - TableName: 1-30 chars, lowercase letters/digits/hyphens, starts with letter
3. Fix the value in `.env` and re-run `/ipa.deploy`.

## Scenario 2: Table Already Exists — Name Collision

**Symptom**: `CREATE_FAILED` with status reason `Table already exists: {table_name}`.

**Cause**: A DynamoDB table with the name `{Namespace}_{Environment}_{TableName}` already exists outside of CloudFormation management (created manually or by another tool).

**Fix**:
1. If the existing table is not needed: delete it manually via `aws dynamodb delete-table --table-name {table_name}`.
2. If the existing table must be kept: change `TableName` in `.env` to a unique name (e.g., `APP_DDB_TABLE_PASSENGERS=passengers-v2`).
3. If the table was created by a previous stack that is in `ROLLBACK_COMPLETE`: delete the failed stack first: `aws cloudformation delete-stack --stack-name {stack-name}`, wait for deletion, then re-deploy.
4. Re-run `/ipa.deploy`.

## Scenario 3: Stack Deletion Fails — Table in Use

**Symptom**: `DELETE_FAILED` with status reason mentioning the table resource.

**Cause**: The table may have deletion protection enabled, or another stack references the table ARN via CloudFormation exports.

**Fix**:
1. Check if deletion protection is enabled: `aws dynamodb describe-table --table-name {table_name} --query 'Table.DeletionProtectionEnabled'`.
2. If deletion protection is on: `aws dynamodb update-table --table-name {table_name} --no-deletion-protection-enabled`.
3. Check for CloudFormation export consumers: `aws cloudformation list-imports --export-name {stack-name}-TableArn`. If other stacks import this export, delete those stacks first.
4. Re-run teardown: `make -f scripts/deploy.mk teardown-ddb-{model}` (e.g., `teardown-ddb-passengers`).

## Scenario 4: "No Updates Are to Be Performed"

**Symptom**: Deploy succeeds but outputs message `No updates are to be performed`.

**Cause**: No parameter values have changed since the last deployment. CloudFormation detects no diff.

**Fix**: This is expected behavior, not an error. The `--no-fail-on-empty-changeset` flag ensures the deploy command exits 0. No action needed.
