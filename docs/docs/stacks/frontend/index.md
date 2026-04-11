---
title: Overview
sidebar_position: 1
---

# Frontend

The frontend stack deploys a secure static web hosting tier using Amazon S3, Amazon CloudFront, and Origin Access Control (OAC). It is designed to serve a React single-page application (SPA) behind a global CDN. The stack enforces HTTPS-only access, restricts all direct bucket access through OAC, and streams access logs to a centralized log bucket. No public bucket access is permitted at any time.

## Features

- **Private S3 bucket** with Block Public Access enabled and AES256 server-side encryption
- **CloudFront CDN** with Origin Access Control using sigv4 request signing
- **HTTPS-only** viewer policy with a minimum TLS version of TLSv1.2_2021
- **SPA routing** via custom error responses that redirect 403 and 404 errors to `index.html` with a 200 status code, allowing the client-side router to handle all paths
- **Access logging** for both S3 and CloudFront to a centralized log bucket provisioned by the security stack
- **No IAM capabilities required** -- the stack creates no IAM roles or policies

## When to Use

Include the frontend stack when the deployment pattern requires a static frontend application. It is provisioned automatically as part of the `react-rest-lambda` pattern. The stack handles only the hosting infrastructure: the S3 bucket, CloudFront distribution, OAC, and bucket policy. Post-deploy phases handle the frontend build upload (`aws s3 sync`), CDN cache invalidation, and Cognito callback URL wiring. If the application does not include a browser-based frontend, this stack is not needed.
