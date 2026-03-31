# Troubleshooting: ipa.stack.apigw

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails — deployment conflict | `deploy-apigw` fails with "Another Deployment is in progress for the RestApi" | API Gateway allows only one deployment at a time. A previous deployment may still be in progress or stuck. | Wait 1-2 minutes and retry. If stuck, check CloudFormation events: `aws cloudformation describe-stack-events --stack-name {APP_NAMESPACE}-{APP_ENV}-apigw`. Delete the stack and recreate if deployment is in a bad state. |
| 2 | All routes return 401 Unauthorized | Every request (including health) returns `{"message": "Unauthorized"}` from API Gateway (not Lambda) | The Cognito authorizer is rejecting the token. Either `UserPoolArn` does not match the deployed Cognito stack, the token is expired, or the Authorization header is missing/malformed. | Verify `UserPoolArn` matches: `aws cloudformation describe-stacks --stack-name {APP_NAMESPACE}-{APP_ENV}-cognito --query 'Stacks[0].Outputs[?OutputKey==\`UserPoolArn\`].OutputValue' --output text`. Ensure the request includes `Authorization: Bearer {id_token}` (ID token, not access token). |
| 3 | Routes return 403 Forbidden | Request returns `{"message": "Forbidden"}` | Missing `AWS::Lambda::Permission` — API Gateway cannot invoke the Lambda function. This can happen if the Lambda stack was redeployed after the API Gateway stack, replacing the function and invalidating the permission. | Redeploy the API Gateway stack: `make -f scripts/deploy.mk deploy-apigw`. This recreates the Lambda permission resources. |
| 4 | Proxy routes return 5xx | `/{proxy+}` routes return 502 Bad Gateway or 500 Internal Server Error | The Lambda function is failing. API Gateway returns 502 when Lambda returns a malformed response, and 500 for unhandled errors. The issue is in the Lambda, not API Gateway. | Check Lambda logs: `aws logs tail /aws/lambda/{APP_NAMESPACE}-{APP_ENV}-fn --since 5m`. Common causes: missing environment variables (AUTH_ISSUER, TABLE_NAME), cold start timeout, or application error. |
| 5 | CORS preflight fails | Browser console shows "blocked by CORS policy" on preflight (OPTIONS) request | The OPTIONS MOCK integration is not returning the expected CORS headers. This can happen if the template was modified incorrectly, or if the request path does not match any resource (`/{proxy+}` does not match the root `/`). | Verify OPTIONS methods exist: `aws apigateway get-resources --rest-api-id {RestApiId} --query 'items[*].resourceMethods.OPTIONS'`. Note that root `/` and `/{proxy+}` have separate OPTIONS methods — both must exist. |
| 6 | SSE routes return 500 | `/api/v1/sse/{proxy+}` requests return 500 Internal Server Error | The streaming Lambda is not deployed with `InvokeMode=RESPONSE_STREAM`, or the `StreamingLambdaFunctionArn` parameter was empty (SSE resources not created). | Verify streaming Lambda invoke mode: `aws lambda get-function-configuration --function-name {APP_NAMESPACE}-{APP_ENV}-fn-stream --query 'InvokeMode'`. Verify SSE resources exist: `aws apigateway get-resources --rest-api-id {RestApiId}` should show `/api/v1/sse/{proxy+}`. |
| 7 | Changes not visible after redeploy | Template changes were deployed but the API still serves old responses | `DeploymentHash` was not changed, so CloudFormation did not create a new `AWS::ApiGateway::Deployment` resource. Without a new deployment, the Stage still points to the old configuration. | Verify `DeploymentHash=$(shell date +%s)` is in the Makefile target. Manually force: `aws cloudformation update-stack --stack-name {APP_NAMESPACE}-{APP_ENV}-apigw --use-previous-template --parameters ParameterKey=DeploymentHash,ParameterValue=$(date +%s) ParameterKey=ApiName,UsePreviousValue=true ...` |
| 8 | Stack deletion hangs | `teardown-apigw` hangs at `wait stack-delete-complete` | The REST API stage or deployment is referenced by another resource, or CloudFormation is waiting for in-flight requests to complete. | Check stack events: `aws cloudformation describe-stack-events --stack-name {APP_NAMESPACE}-{APP_ENV}-apigw --query 'StackEvents[?ResourceStatus==\`DELETE_FAILED\`]'`. If a specific resource fails, delete it manually via AWS CLI, then retry the stack deletion. |

## Additional Troubleshooting

### API Gateway returns "Missing Authentication Token"

**Symptom**: Request to `{ApiUrl}/some/path` returns `{"message": "Missing Authentication Token"}`.

**Root Cause**: This is API Gateway's default response when the request path does not match any configured resource. Despite the misleading message, it's a 403 (not found), not an auth error. Common cause: the stage name is wrong or the path has a typo.

**Recovery**: Verify the ApiUrl includes the stage name (e.g., `https://{id}.execute-api.{region}.amazonaws.com/prod/health`). List available resources: `aws apigateway get-resources --rest-api-id {RestApiId}`.

### Cognito domain prefix conflict

**Symptom**: Cognito stack deployment fails before API Gateway can be deployed.

**Root Cause**: This is not an API Gateway issue — it's a prerequisite failure. The Cognito domain prefix must be globally unique.

**Recovery**: See `ipa.stack.cognito/TROUBLESHOOT.md` for Cognito-specific issues. API Gateway deployment depends on a successfully deployed Cognito stack.

### Cold start latency on first request

**Symptom**: First request after deployment takes 10-15 seconds, then subsequent requests are fast.

**Root Cause**: Lambda cold start. The container image needs to be pulled and initialized on the first invocation. This is not an API Gateway issue.

**Recovery**: This is expected behavior. For production, consider provisioned concurrency on the Lambda function (configured in `ipa.stack.lambda`, not API Gateway).
