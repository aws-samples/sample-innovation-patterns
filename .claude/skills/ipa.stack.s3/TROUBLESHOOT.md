# Troubleshooting: ipa.stack.s3

## Failure Catalog

| Symptom | Root Cause | Recovery |
|---------|-----------|----------|
| `BucketAlreadyExists` | Bucket name collision — another account owns this name | Change `BucketNameSuffix` in `.env` or verify `APP_NAMESPACE`/`APP_ENV` are unique |
| `The bucket you tried to delete is not empty` | S3 bucket contains uploaded frontend files | Empty the bucket first: `aws s3 rm s3://{bucket-name} --recursive`, then re-run teardown |
| Stack stuck in `DELETE_FAILED` | Bucket policy or bucket not empty | Empty bucket, remove bucket policy manually, then re-run teardown |
| `Access Denied` on deploy | Missing s3:CreateBucket or s3:PutBucketPolicy permissions | Verify IAM role has permissions scoped to `{ns}-{env}-web-*` |
