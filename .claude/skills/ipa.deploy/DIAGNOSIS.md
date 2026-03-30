# Deployment Failure Diagnosis

Reference file for `/ipa.deploy` — error classification and recovery procedures for CloudFormation deployment failures.

---

## Diagnosis Procedure

When a Make target fails during deployment (exit code ≠ 0):

### 1. Detect the Failed Stack

Read the Make output. The failed stack name is the `--stack-name` value in the `aws cloudformation` command that errored:

```
aws cloudformation deploy \
    --stack-name ipatest-dev-lambda \    ← this is the failed stack
    --template-file infra/cfn/lambda/lambda.yml \
    ...
Error: Stack ipatest-dev-lambda failed...
```

### 2. Read Stack Events

```bash
aws cloudformation describe-stack-events --stack-name {failed-stack-name}
```

Output shows events in chronological order:

```
Timestamp                 Resource              Status              Reason
2026-03-27 10:15:00      LambdaFunction        CREATE_FAILED       not authorized to perform: lambda:CreateFunction
2026-03-27 10:15:01      ipatest-dev-lambda    ROLLBACK_IN_PROGRESS The following resource(s) failed...
```

### 3. Classify the Error

Scan the `Reason` column for text patterns matching the categories below.

---

## Error Classification Table

| Category | Event Text Signals | Recovery Type | Recovery Action |
|----------|-------------------|---------------|-----------------|
| **Permission denied** | "not authorized", "Access Denied", "is not authorized to perform" | Manual | Re-run `/ipa.security` to update IAM permissions for the builder role |
| **Validation error** | "Invalid", "parameter", "not valid", "failed validation", "template error" | Manual | Check the CloudFormation template and parameter values; fix the template or `--parameter-overrides` in `deploy.mk` |
| **Resource conflict** | "already exists", "AlreadyExists" | Manual | Change `APP_NAMESPACE` in `.env` to generate different resource names, or manually delete the conflicting resource |
| **Stuck rollback** | Stack status is `ROLLBACK_COMPLETE` (check via `cfn-status`) | Auto | Delete the failed stack, then retry deployment |
| **Transient / throttle** | "Rate exceeded", "Throttling", "TooManyRequestsException", "ServiceUnavailable" | Auto | Wait 30 seconds, then retry deployment |

If the event text does not match any category, display the raw events to the builder and ask them to investigate.

---

## Auto-Recovery Procedure

For categories marked **Auto** (stuck rollback, transient):

### Stuck Rollback Recovery

1. Explain to the builder: "Stack `{stack-name}` is in `ROLLBACK_COMPLETE` state from a previous failed deployment. I can delete it and retry."
2. Ask: "Would you like me to delete the stuck stack and retry? (yes/no):"
3. If confirmed:

   ```bash
   aws cloudformation delete-stack --stack-name {failed-stack-name}
   aws cloudformation wait stack-delete-complete --stack-name {failed-stack-name}
   ```

4. Wait for deletion to complete (status becomes `DELETE_COMPLETE` or stack no longer exists).
5. Re-run the full deployment:

   ```bash
   make -f scripts/deploy.mk deploy
   ```

### Transient Error Recovery

1. Explain to the builder: "The deployment failed due to a transient AWS error (throttling or service unavailability). This is usually temporary."
2. Ask: "Would you like me to wait 30 seconds and retry? (yes/no):"
3. If confirmed: wait 30 seconds, then re-run:

   ```bash
   make -f scripts/deploy.mk deploy
   ```

---

## Manual Recovery Guidance

For categories marked **Manual** (permission denied, validation error, resource conflict):

### Permission Denied

The builder role does not have sufficient IAM permissions for the operation that failed.

1. Note the specific permission from the event text (e.g., `lambda:CreateFunction`, `ecr:CreateRepository`).
2. Advise: "Run `/ipa.security` to update the builder role's IAM permissions. The security skill will detect the existing security stack and offer to update it."
3. After the builder updates permissions, re-run `/ipa.deploy`.

### Validation Error

The CloudFormation template or parameter values are invalid.

1. Display the specific validation error from the event text.
2. Advise: "Check the CloudFormation template referenced in the error. Verify parameter names and types match the template's `Parameters` section."
3. If the error is in `--parameter-overrides`, advise re-running `/ipa.compose` to regenerate `deploy.mk` with corrected parameters.

### Resource Conflict

A resource with the same name already exists (not managed by this stack).

1. Display the conflicting resource name from the event text.
2. Advise: "Either change `APP_NAMESPACE` in `.env` (then re-run `/ipa.compose` and `/ipa.deploy`), or manually delete the conflicting resource in the AWS Console."
