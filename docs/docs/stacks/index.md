---
title: Overview
sidebar_position: 1
---

# Stacks

IPA stacks are CloudFormation-based infrastructure components that compose into deployable solutions. Each stack wraps one or more AWS services with security defaults, observability, and a consistent parameter interface.

Stacks fall into two lifecycle categories:

- **Prepare stacks** are one-time prerequisites that persist across teardown and redeployment cycles. Deploy them once with `/ipa.prepare`.
- **Deploy stacks** (tiers) are application infrastructure created and torn down with each pattern deployment via `/ipa.deploy`.

## Deploy Stacks (Tiers)

- **[Frontend](frontend/)** — S3 + CloudFront with Origin Access Control for static web hosting.
- **[Backend](backend/)** — Lambda + API Gateway v2 + DynamoDB + CloudWatch for serverless APIs.
- **[Queue](queue/)** — SQS + DLQ + worker Lambda + EventSourceMapping + DynamoDB + CloudWatch for event-driven processing.

## Prepare Stacks

- **[Cognito](cognito/)** — Cognito User Pool with OAuth 2.0 Hosted UI and OIDC endpoints for authentication.
- **[ECR](ecr/)** — Elastic Container Registry repository for Lambda container images.
- **[CodePipeline](codepipeline/)** — CodePipeline + CodeBuild for CI/CD automation.
- **[CodeCommit](codecommit/)** — CodeCommit repository for source code management.
