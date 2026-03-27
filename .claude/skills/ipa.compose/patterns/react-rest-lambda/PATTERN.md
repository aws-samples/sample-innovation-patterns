# Pattern: react-rest-lambda

Full-stack serverless web application pattern. Deploys a React frontend served via CloudFront, REST API through API Gateway, Lambda compute with container images from ECR, DynamoDB for data storage, and Cognito for authentication.

## Stack Sequence

1. ipa.stack.ecr — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

## Teardown Sequence

1. ipa.stack.ecr (suffix: ecr)

## Wiring

wiring: []
# No wiring entries yet — ECR's downstream consumers (Lambda) don't exist.
# When Spec 4 (Lambda) is implemented, 2 entries will be added here.

## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| (none yet) | | |
