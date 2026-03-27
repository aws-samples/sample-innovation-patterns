# Security Advisory: ipa.stack.ecr

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the ECR stack.

```yaml
permissions:
  - actions:
      - ecr:CreateRepository
      - ecr:DeleteRepository
      - ecr:DescribeRepositories
      - ecr:TagResource
      - ecr:UntagResource
      - ecr:ListTagsForResource
      - ecr:PutImageTagMutability
      - ecr:SetRepositoryPolicy
      - ecr:DeleteRepositoryPolicy
    resource: "arn:aws:ecr:{AWS_REGION}:{AWS_ACCOUNT_ID}:repository/{APP_NAMESPACE}-{APP_ENV}-ecr"
    purpose: "CloudFormation CRUD operations on ECR repository resource"

  - actions:
      - ecr:GetAuthorizationToken
    resource: "*"
    purpose: "Required for ECR authentication — this action does not support resource-level permissions (AWS API limitation)"
```

## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks at runtime. These are **not** consumed by the Builder Execution Role — they are advisory for stacks that integrate with ECR (e.g., Lambda functions pulling container images).

```yaml
runtime_permissions:
  - actions:
      - ecr:BatchGetImage
      - ecr:GetDownloadUrlForLayer
    resource: "!Output RepositoryArn"
    purpose: "Runtime image pull by consuming Lambda execution roles"
```

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.

```yaml
controls:
  - type: encryption
    enabled: true
    method: "AES256 encryption at rest — ECR default server-side encryption"

  - type: access_control
    enabled: true
    method: "No public access — repository is private by default, no repository policy grants cross-account or public access"

  - type: deletion_safety
    enabled: true
    method: "No ForceDelete — stored images must be manually removed before stack deletion (prevents accidental data loss)"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No lifecycle policy | POC scope — can be added later without breaking wiring | Low — manual image cleanup is documented in TROUBLESHOOT.md |
| No image scanning | POC scope — ECR basic scanning defaults are sufficient | Low — can be enabled via console or future template update |
| ImageTagMutability: MUTABLE | POC simplification — allows tag overwrite for rapid iteration | Low — switch to IMMUTABLE for production via parameter |
