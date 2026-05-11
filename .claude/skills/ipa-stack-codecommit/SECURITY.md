# Security Advisory: ipa-stack-codecommit

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the CodeCommit stack.

```yaml
permissions:
  - actions:
      - codecommit:CreateRepository
      - codecommit:DeleteRepository
      - codecommit:GetRepository
      - codecommit:UpdateRepositoryDescription
      - codecommit:TagResource
      - codecommit:UntagResource
    resource: "arn:aws:codecommit:{AWS_REGION}:{AWS_ACCOUNT_ID}:{RepositoryName}"
    purpose: "CloudFormation CRUD operations on CodeCommit repository resource"

  - actions:
      - kms:DescribeKey
      - kms:CreateGrant
    resource: "{KmsKeyArn}"
    condition: "Only when KmsKeyArn parameter is provided (HasKmsKey condition)"
    purpose: "KMS key access for repository encryption at rest"
```

## Security Controls

Controls enforced by the CloudFormation template.

```yaml
controls:
  - type: access_control
    enabled: true
    method: "No public access — CodeCommit repositories are private by default, accessible only via IAM-authenticated Git credentials"

  - type: encryption
    enabled: conditional
    method: "Optional KMS encryption at rest via KmsKeyArn parameter. When not provided, CodeCommit uses AWS-managed encryption"

  - type: lifecycle_safety
    enabled: true
    method: "Repository is a separate stack from the pipeline — deleting the pipeline stack does not affect the repository"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No branch protection rules | POC scope — can be configured manually via console | Low — single developer workflow |
| No approval rules | POC scope — not needed for single-environment deployment | Low |
