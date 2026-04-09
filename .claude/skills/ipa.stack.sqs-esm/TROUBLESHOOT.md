# Troubleshooting: ipa.stack.sqs-esm

## Scenario 1: Stack Creation Fails — Lambda Permission Error

**Symptom**: `CREATE_FAILED` with status reason "An error occurred (InvalidParameterValueException) when calling the CreateEventSourceMapping operation: The provided execution role does not have permissions to call ReceiveMessage on SQS".

**Cause**: The Lambda function's execution role does not have `sqs:ReceiveMessage` permission on the target SQS queue ARN. The `SqsReceiveQueueArns` parameter was not wired correctly when deploying the Lambda stack.

**Fix**:
1. Verify the Lambda function has SQS receive permissions: `aws lambda get-function-configuration --function-name {APP_NAMESPACE}-{APP_ENV}-fn-worker --query 'Role'`, then check the role's policies.
2. Ensure `SqsReceiveQueueArns` is wired from `ipa.stack.sqs` `QueueArn` in the compose configuration.
3. Re-run `/ipa.compose` to regenerate deploy.mk with correct wiring, then redeploy the Lambda stack before the ESM stack.

## Scenario 2: Stack Creation Fails — Queue Not Found

**Symptom**: `CREATE_FAILED` with status reason referencing an invalid or non-existent queue ARN.

**Cause**: The SQS queue stack was not deployed, or the `QueueArn` parameter value is incorrect.

**Fix**:
1. Verify the SQS stack exists: `aws cloudformation describe-stacks --stack-name {APP_NAMESPACE}-{APP_ENV}-sqs --query 'Stacks[0].StackStatus'`.
2. If the stack does not exist, deploy it first: `make -f scripts/deploy.mk deploy-sqs`.
3. If the stack exists, verify the output: `aws cloudformation describe-stacks --stack-name {APP_NAMESPACE}-{APP_ENV}-sqs --query 'Stacks[0].Outputs[?OutputKey==\`QueueArn\`].OutputValue' --output text`.
4. Re-run `/ipa.compose` and redeploy.

## Scenario 3: Stack Deletion Hangs

**Symptom**: `teardown-esm` hangs or ESM stack deletion takes unusually long.

**Cause**: Active Lambda invocations triggered by the event source mapping are still in progress. CloudFormation waits for the ESM to be fully disabled and all in-flight invocations to complete.

**Fix**:
1. The ESM is automatically disabled during deletion — wait for in-flight invocations to complete.
2. If deletion is stuck for more than 10 minutes, check the event source mapping state: `aws lambda list-event-source-mappings --function-name {APP_NAMESPACE}-{APP_ENV}-fn-worker`.
3. Manually disable the mapping if needed: `aws lambda update-event-source-mapping --uuid {mapping-uuid} --no-enabled`.
4. Retry the stack deletion.

## Scenario 4: Messages Not Being Processed

**Symptom**: Messages accumulate in the SQS queue but the Lambda function is not being invoked.

**Cause**: The event source mapping may be disabled, or the mapping was not created successfully.

**Fix**:
1. Check the mapping state: `aws lambda list-event-source-mappings --function-name {APP_NAMESPACE}-{APP_ENV}-fn-worker --query 'EventSourceMappings[*].{UUID:UUID,State:State,Enabled:Enabled}'`.
2. If the state is `Disabled`, enable it: update the `Enabled` parameter to `true` and redeploy.
3. If no mapping exists, verify the ESM stack deployed successfully: `aws cloudformation describe-stacks --stack-name {APP_NAMESPACE}-{APP_ENV}-esm`.
4. Re-run `/ipa.deploy` if the stack is missing or in a failed state.
