---
title: Overview
sidebar_position: 1
---

# ECR

The ECR stack deploys a single Amazon Elastic Container Registry repository for storing Lambda container images. It is a prepare-lifecycle stack, meaning it is created once and persists across application deployments. Backend and queue tier stacks reference the repository URI when deploying container-packaged Lambda functions.

## Features

- **Scan-on-push** vulnerability scanning for every image pushed to the repository
- **AES256 encryption** at rest using Amazon S3-managed server-side encryption
- **Mutable image tags** allowing in-place tag updates during iterative development
- **No automatic deletion** on stack removal -- the repository and its images are retained by default, preventing accidental data loss
- **No IAM capabilities required** -- the stack creates no IAM roles or policies

## When to Use

Include the ECR stack when the deployment pattern uses container-packaged Lambda functions. It is provisioned automatically as part of the `react-rest-lambda` pattern's prepare phase. The stack provides the `RepositoryUri` output consumed by the backend and queue tiers to resolve the Lambda `ImageUri` at deploy time. If the application uses only zip-packaged Lambda functions or does not include a Lambda backend, this stack is not needed.
