# Security Advisory: ipa.stack.sqs-esm

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage this stack.

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| `lambda:CreateEventSourceMapping` | `*` | Create the SQS-to-Lambda mapping |
| `lambda:DeleteEventSourceMapping` | `*` | Stack teardown |
| `lambda:GetEventSourceMapping` | `*` | CloudFormation status checks |
| `lambda:UpdateEventSourceMapping` | `*` | Update batch size, window, or enabled state |

**Note on `*` resource scope**: Event source mapping ARNs include a UUID that is not known at deploy time. AWS does not support resource-level scoping for ESM operations. This is a documented AWS IAM limitation.

## Runtime Permissions (Advisory)

This stack does not create any IAM resources. The Lambda function's execution role must already have SQS receive permissions (`sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`, `sqs:ChangeMessageVisibility`) on the target queue ARN. These permissions are granted by `ipa.stack.lambda` when `SqsReceiveQueueArns` is wired.

## Security Controls (Hardcoded)

| Control | Setting | Notes |
|---------|---------|-------|
| No additional IAM | None created | Lambda execution role manages all permissions |
| Deployment ordering | ESM deployed last, torn down first | Prevents orphaned triggers |

## Known Deferrals

| Deferral | Rationale |
|----------|-----------|
| No `*` resource scope mitigation | AWS limitation — ESM ARNs include unpredictable UUIDs. Accepted for all tiers. |
