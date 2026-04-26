# infra/cfn/codecommit/

CodeCommit repository template for IPA source code management. Deployed by `/ipa.codepipeline` process skill.

## Resources

| Resource | Type | Description |
|----------|------|-------------|
| Repository | `AWS::CodeCommit::Repository` | Source code repository with optional KMS encryption |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Namespace | Yes | — | Project namespace prefix |
| Environment | Yes | — | Environment name |
| RepositoryName | Yes | — | Repository name (`[a-zA-Z0-9._-]+`) |
| RepositoryDescription | No | `IPA-managed source repository` | Human-readable description |
| KmsKeyArn | No | *(empty)* | Customer-managed KMS key ARN |

## Conditions

- `HasKmsKey`: Enables KMS encryption when `KmsKeyArn` is non-empty

## Security Controls

- Optional KMS encryption at rest (via `HasKmsKey` condition)
- No public access (CodeCommit repositories are private by default)

## Outputs

- `RepositoryName`, `RepositoryArn`, `CloneUrlHttp` — all exported as `{StackName}-{OutputKey}`

## Stack Naming

`{APP_NAMESPACE}-{APP_ENV}-codecommit`

## Related

- Stack skill: `.claude/skills/ipa.stack.codecommit/`
- Process skill: `.claude/skills/ipa.codepipeline/`
- Consumed by: `infra/cfn/codepipeline/codepipeline.yml` (Source stage references repository name)
