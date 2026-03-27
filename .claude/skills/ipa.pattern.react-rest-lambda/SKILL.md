---
name: ipa-pattern-react-rest-lambda
description: "Full-stack web application: React frontend, REST API via API Gateway, Lambda compute, DynamoDB storage, Cognito auth, CloudFront CDN."
---

# ipa.pattern.react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, REST API through API Gateway, Lambda compute with container images from ECR, DynamoDB for data storage, and Cognito for authentication.

## Composition Type

standalone

## Stack Sequence

1. ipa.stack.ecr — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

## Teardown Sequence

1. ipa.stack.ecr (suffix: ecr)

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| (none yet) | | |
