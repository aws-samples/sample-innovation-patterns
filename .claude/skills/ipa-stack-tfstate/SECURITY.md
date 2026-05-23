# Security Advisory: ipa-stack-tfstate

## Overview

The Terraform state backend stores sensitive infrastructure state including resource ARNs, IP addresses, and potentially secrets embedded in resource configurations. This stack provides the minimal secure foundation for Terraform state management.

## Security Controls

| Control | Implementation | Rationale |
|---------|---------------|-----------|
| Encryption at rest (S3) | AES256 server-side encryption | State files may contain sensitive resource metadata |
| Encryption at rest (DynamoDB) | SSE enabled | Lock entries contain state file paths |
| Versioning | S3 versioning enabled | Recovery from accidental state corruption |
| Public access block | All four S3 public access settings enabled | State files must never be publicly accessible |
| TLS-only | Bucket policy denies non-SSL requests | Prevent state exposure over unencrypted connections |
| Point-in-time recovery | DynamoDB PITR enabled | Recovery from accidental lock table corruption |
| Deletion protection | `DeletionPolicy: Retain` on both resources | Prevent accidental state loss during stack teardown |

## IAM Permissions Required

The deploying principal needs:

```yaml
s3:
  - CreateBucket
  - PutBucketVersioning
  - PutBucketEncryption
  - PutBucketPublicAccessBlock
  - PutBucketPolicy
  - GetBucketPolicy
dynamodb:
  - CreateTable
  - DescribeTable
  - UpdateTable
  - UpdateContinuousBackups
  - TagResource
```

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| State file contains secrets | Medium | Use `sensitive` attribute in TF modules; enable S3 encryption |
| Bucket name guessable | Low | Includes account ID and region for uniqueness |
| Lock table DoS | Low | PAY_PER_REQUEST billing prevents cost issues |
| Accidental deletion | High | DeletionPolicy: Retain on both resources |

## POC Scope Deferrals

| Finding | Rationale |
|---------|-----------|
| No KMS CMK encryption | POC scope — AES256 is sufficient; CMK adds key management overhead |
| No S3 Object Lock | POC scope — versioning provides adequate protection |
| No cross-region replication | POC scope — single-region deployment |
| No bucket access logging | POC scope — state access is through Terraform CLI only |
