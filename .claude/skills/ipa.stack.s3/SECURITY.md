# Security Advisory: ipa.stack.s3

## Deployment Permissions

IAM actions required to deploy/update/delete this stack:

| Action | Resource Scope | Purpose |
|--------|---------------|---------|
| s3:CreateBucket | `arn:aws:s3:::{ns}-{env}-web-*` | Create the web hosting bucket |
| s3:DeleteBucket | `arn:aws:s3:::{ns}-{env}-web-*` | Stack teardown |
| s3:PutBucketEncryption | `arn:aws:s3:::{ns}-{env}-web-*` | Enable SSE-S3 |
| s3:PutBucketPolicy | `arn:aws:s3:::{ns}-{env}-web-*` | Attach bucket policy |
| s3:PutPublicAccessBlock | `arn:aws:s3:::{ns}-{env}-web-*` | Block all public access |
| s3:PutBucketTagging | `arn:aws:s3:::{ns}-{env}-web-*` | Apply resource tags |

## Runtime Permissions

Advisory — permissions for services that interact with the bucket at runtime:

| Action | Resource Scope | Granted To | Purpose |
|--------|---------------|------------|---------|
| s3:GetObject | `arn:aws:s3:::{bucket}/*` | CloudFront OAC | Serve static assets |

Note: CloudFront OAC access is granted via bucket policy in the CloudFront stack, not this stack.

## Security Controls

| Control | Implementation |
|---------|---------------|
| No public access | `PublicAccessBlockConfiguration` — all four settings enabled |
| Encryption at rest | SSE-S3 (AES-256) |
| No static website hosting | Bucket serves content only via CloudFront OAC |
| Deleted on teardown | `DeletionPolicy: Delete` — bucket removed when stack is deleted (post-deploy destroy empties it first) |

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| S3-1 | No bucket versioning | POC scope — versioning adds cost and complexity; production should enable it |
| S3-2 | No lifecycle rules | POC scope — production should add expiration policies for old versions |
| S3-3 | DeletionPolicy: Delete | Teardown requires bucket to be emptied first; post-deploy destroy handles this |
