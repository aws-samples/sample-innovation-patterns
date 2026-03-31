# Troubleshooting: ipa.stack.cloudfront

## Failure Catalog

| Symptom | Root Cause | Recovery |
|---------|-----------|----------|
| Distribution returns 403 Access Denied | Bucket policy missing or OAC not configured | Verify CloudFront stack deployed successfully and bucket policy includes `AllowCloudFrontOAC` statement |
| Distribution returns 403 for all paths | S3 bucket is empty (no files uploaded) | Run `make -f scripts/build.mk build-frontend` then post-deploy to upload files |
| SPA routes return CloudFront error page | Custom error responses not configured (403/404 -> /index.html) | Verify template has `CustomErrorResponses` for both 403 and 404 |
| Stack creation takes 15+ minutes | Normal — CloudFront distribution creation is slow | Wait for completion; do not cancel and retry (creates orphaned distributions) |
| Stack deletion hangs | Distribution must be disabled before deletion | CloudFormation handles this automatically but it takes 15-30 minutes |
| `CNAMEAlreadyExists` | Custom domain already associated with another distribution | Not applicable for POC (no custom domain) — would need to disassociate first |
| Changes not visible after deploy | CloudFront caching old content | Run `make -f scripts/post-deploy.mk invalidate-cf` or wait for TTL expiry (5 min default) |
| `The S3 bucket that you specified for CloudFront logs does not exist` | Access logging misconfigured | Not applicable for POC (no access logging configured) |
