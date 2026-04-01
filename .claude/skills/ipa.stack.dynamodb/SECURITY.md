# Security Advisory: ipa.stack.dynamodb

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage this stack.

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| `dynamodb:CreateTable` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | Create the table |
| `dynamodb:DeleteTable` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | Stack teardown |
| `dynamodb:DescribeTable` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | CloudFormation status checks |
| `dynamodb:UpdateTable` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | Billing mode or attribute changes |
| `dynamodb:TagResource` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | Apply tags |
| `dynamodb:UntagResource` | `arn:aws:dynamodb:{region}:{account}:table/{ns}_{env}_*` | Remove tags |

## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks (e.g., Lambda) to interact with the table at runtime. These are NOT required for deployment — they belong in the consuming stack's execution role.

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| `dynamodb:PutItem` | `{TableArn}` | Write records |
| `dynamodb:GetItem` | `{TableArn}` | Read single record by key |
| `dynamodb:Query` | `{TableArn}` | Query records by partition key |
| `dynamodb:Scan` | `{TableArn}` | Full table scan |
| `dynamodb:DeleteItem` | `{TableArn}` | Delete single record |
| `dynamodb:UpdateItem` | `{TableArn}` | Update single record |

## Security Controls (Hardcoded)

| Control | Setting | Notes |
|---------|---------|-------|
| Encryption at rest | SSE enabled (AWS-owned key) | No KMS key management overhead for POC |
| Public access | None | IAM-only access, no public endpoints |
| Billing mode | PAY_PER_REQUEST (default) | No capacity planning risk for POC |

## Known Deferrals

| Deferral | Rationale |
|----------|-----------|
| No Point-In-Time Recovery (PITR) | POC scope — data is ephemeral |
| No Global Secondary Indexes (GSI) | POC scope — partition key covers initial access patterns |
| No DynamoDB Streams | Streaming is a Lambda concern, not a table concern |
| No backup configuration | POC scope — production backup is customer responsibility |
| No DeletionPolicy: Retain | Clean teardown preferred for POC; data loss prevention is not critical |
