---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The frontend stack is included automatically when composing the `react-rest-lambda` pattern. Run the compose skill and select the pattern when prompted:

    /ipa.compose

Select `react-rest-lambda` when prompted. The compose process generates the deployment Makefile targets and wires the frontend stack into the correct deploy order.

## Configuration

The following `.env` variables map to the stack parameters:

| Parameter | `.env` Variable | Required | Default | Description |
|-----------|----------------|----------|---------|-------------|
| Namespace | `APP_NAMESPACE` | Yes | -- | Project namespace prefix for resource naming. Must match `^[a-z][a-z0-9-]{0,11}$`. |
| Environment | `APP_ENV` | Yes | -- | Deployment environment (`dev`, `staging`, or `prod`). |
| BucketNameSuffix | -- | No | `web` | Suffix appended to the bucket name. The full bucket name follows the pattern `{ns}-{env}-{suffix}-{account_id}`. |
| LogBucketDomainName | -- | Yes | -- | S3 domain name of the centralized log bucket (e.g., `{bucket}.s3.amazonaws.com`). Resolved from the security stack output. |

## Outputs

The stack exports the following values for use by post-deploy steps and other stacks:

| Output | Export Name | Description |
|--------|------------|-------------|
| AppUrl | `{StackName}-AppUrl` | CloudFront HTTPS URL serving as the application entry point. Used by `configure-frontend` and Cognito callback wiring. |
| DistributionId | `{StackName}-DistributionId` | CloudFront distribution ID. Used by the `invalidate-cf` post-deploy step to clear the CDN cache. |
| DistributionDomainName | `{StackName}-DistributionDomainName` | CloudFront domain name. Used for Cognito callback URL configuration. |
| BucketName | `{StackName}-BucketName` | S3 bucket name. Used by the `upload-frontend` post-deploy step as the `aws s3 sync` target. |
