# Security Advisory: ipa-stack-logs

## Resource Inventory

| Resource | Type | Access | Encryption |
|----------|------|--------|------------|
| LogBucket | AWS::S3::Bucket | Private (all public access blocked) | SSE-S3 (AES-256) |
| LogBucketPolicy | AWS::S3::BucketPolicy | Scoped to AWS service principals | N/A |

## Bucket Policy Statements

| Sid | Principal | Action | Resource Scope | Condition |
|-----|-----------|--------|---------------|-----------|
| AllowS3ServerAccessLogs | logging.s3.amazonaws.com | s3:PutObject | `{bucket}/s3-access-logs/*` | aws:SourceAccount |
| AllowCloudFrontLogs | cloudfront.amazonaws.com | s3:PutObject | `{bucket}/cloudfront-logs/*` | aws:SourceAccount |
| AllowVPCFlowLogs | delivery.logs.amazonaws.com | s3:PutObject | `{bucket}/vpc-flow-logs/*` | aws:SourceAccount |
| DenyNonSSL | * | s3:* (Deny) | `{bucket}` + `{bucket}/*` | aws:SecureTransport=false |

## Security Controls

- **Public Access**: All four public-access-block settings enabled
- **Encryption**: SSE-S3 (AES-256); KMS optional via `KmsKeyArn` parameter
- **Versioning**: Enabled (prevents accidental deletion of log data)
- **Lifecycle**: 90-day expiration (POC — adjust for production retention requirements)
- **Ownership**: BucketOwnerPreferred (required for S3 access log delivery)
- **TLS**: Deny all non-SSL requests

## IAM Actions Required for Deployment

```
s3:CreateBucket
s3:DeleteBucket
s3:PutBucketPolicy
s3:PutBucketVersioning
s3:PutEncryptionConfiguration
s3:PutLifecycleConfiguration
s3:PutBucketPublicAccessBlock
s3:PutBucketOwnershipControls
s3:PutBucketTagging
```

All scoped to `arn:aws:s3:::{namespace}-{environment}-logs-{account}-{region}`.

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Log data exfiltration | Public access blocked, TLS enforced, SourceAccount condition |
| Unauthorized writes | Bucket policy limits PutObject to specific AWS service principals |
| Data retention | 90-day lifecycle; adjust for compliance requirements |
| Bucket name collision | Globally unique via account ID + region suffix |
