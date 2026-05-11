# Troubleshooting: ipa-stack-cognito

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Domain prefix conflict | `deploy-cognito` fails with "Domain already exists" or "CustomDomainIsNotAllowed" | Cognito domain prefixes are globally unique across all AWS accounts. Another account is using this prefix. | Change `CognitoDomainPrefix` to a different value. Convention: `{namespace}-{env}-{hash}` (where `{hash}` is `APP_ACCOUNT_HASH` from `.env`). If still conflicting, append a random suffix (e.g., `-01`). |
| 2 | ROLLBACK_COMPLETE | Stack shows status `ROLLBACK_COMPLETE` and cannot be updated | Initial stack creation failed (often a domain conflict or invalid parameter). CloudFormation rolled back but cannot delete the failed stack automatically. | Delete the failed stack: `aws cloudformation delete-stack --stack-name {stack-name}`. Fix the root cause (check CloudFormation Events for the specific error), then re-deploy. |
| 3 | Callback URL mismatch | Cognito login redirects to the Hosted UI but the callback fails with "redirect_mismatch" error | The `CallbackURL` parameter in the Cognito stack does not match the actual frontend URL or the OIDC client's `redirect_uri`. | Update the Cognito stack with the correct `CallbackURL` value. For two-phase deploys, ensure the second deploy runs after CloudFront/frontend is deployed. Verify the URL includes the full path (e.g., `https://d1234.cloudfront.net/authentication/callback`). |
| 4 | Reserved word in prefix | Domain creation fails with "InvalidParameterException" referencing the domain prefix | The `CognitoDomainPrefix` contains one of Cognito's reserved words: `cognito`, `aws`, or `amazon`. | Change the namespace, environment, or prefix to avoid reserved words. Check that `{namespace}-{env}-{hash}` does not contain these substrings. If the namespace itself contains a reserved word, choose a different namespace. |
| 5 | ManagedLoginBranding failure | Stack creation fails on the `ManagedLoginBranding` resource with "ResourceNotFound" or similar error | The `ManagedLoginBranding` resource requires the Cognito domain to be fully created first. In rare cases, the resource type may not be available in the target AWS region. | Verify the template has `DependsOn: CognitoUserPoolDomain` on the `ManagedLoginBranding` resource (this is already set in the template). If the error persists, check that the region supports `AWS::Cognito::ManagedLoginBranding`. As a last resort, remove the `ManagedLoginBranding` resource from the template for that region. |

## Additional Troubleshooting

### API returns 401 after enabling auth

**Symptom**: All API calls return 401 Unauthorized after connecting Cognito to API Gateway.

**Root Cause**: The Lambda function does not have `AUTH_ISSUER` and `AUTH_AUDIENCE` environment variables set, or the API Gateway authorizer is not configured with the correct User Pool ARN.

**Recovery**: Verify that the Lambda stack was deployed with the Cognito outputs wired correctly:
- `AuthIssuer` parameter = Cognito `IssuerUrl` output
- `AuthAudience` parameter = Cognito `UserPoolClientId` output
- API Gateway `CognitoUserPoolArn` parameter = Cognito `UserPoolArn` output

### Stack update fails with "No updates are to be performed"

**Symptom**: `aws cloudformation deploy` exits with an error about no updates.

**Root Cause**: The parameters and template have not changed since the last deployment.

**Recovery**: This is not an error — the stack is already in the desired state. The `aws cloudformation deploy --no-fail-on-empty-changeset` flag handles this gracefully and should not report it as a failure.
