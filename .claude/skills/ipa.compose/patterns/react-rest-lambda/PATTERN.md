# Pattern: react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, REST API through API Gateway, Lambda compute with container images from ECR, DynamoDB for data storage, and Cognito for authentication.

## Stack Sequence

1. ipa.stack.ecr (prepare) — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

2. ipa.stack.cognito — Cognito User Pool for authentication
   - Depends on: none
   - Suffix: cognito

## Teardown Sequence

1. ipa.stack.cognito (suffix: cognito)

## Wiring

wiring: []
# No wiring entries yet — ECR's downstream consumers (Lambda) don't exist.
# When Spec 4 (Lambda) is implemented, 2 entries will be added here.

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| (none yet) | | |
