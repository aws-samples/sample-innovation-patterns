# Credential vendor role

The IAM role this repository's GitLab CI jobs assume to reach AWS with no long-lived key.
Deployed once, by hand, per target account. Internal maintainer tooling — not shipped.

Its only purpose is to let a CI job do what `make -C ../codepipeline trigger` does: upload
a source archive, start one pipeline execution, and read the result.

## This may already be unnecessary

`.gitlab-ci.yml:32-43` carries a commented-out job documenting the mechanism and naming a
role that **already exists**:

```yaml
AWS_CREDS_TARGET_ROLE: arn:aws:iam::369530416671:role/ip-dev-sdlc-GitLab
```

That role was provisioned by the SDLC account vending, not by this repository. If it can
already start the pipeline, this stack is redundant — check its policy before deploying a
second role. This template exists for the case where it cannot, or where the pipeline
lives in a different account.

## How the credentials arrive (two hops, two accounts)

| Hop | What happens |
|---|---|
| 1 | The vendor reads the job's `CI_JOB_TOKEN` and assumes a role in jump account `979517299116`, which attaches the job's GitLab metadata as **principal tags** — derived from the real running job, not supplied by the caller. |
| 2 | It presents `arn:aws:iam::352364310414:role/prod_jump_role` to **this** role, with a `RoleSessionName` of `<alias>-GitLab` for CloudTrail. |

Only the hop-2 role is a trust-policy principal. Naming the hop-1 account instead produces
a role that deploys cleanly, reports success, and fails only when a CI job first tries to
assume it.

The internal `code.aws.dev` runner does this automatically when `AWS_CREDS_TARGET_ROLE` is
set. No `id_tokens` block and no explicit assume-role step are needed.

## What this role can and cannot do

**Can:** `s3:PutObject` on exactly one key; `s3:GetBucketVersioning`;
`codepipeline:StartPipelineExecution` and three read actions on one pipeline;
`codebuild:BatchGetBuilds`/`BatchGetReports`/`DescribeTestCases` and three `logs:` read
actions, scoped by the pipeline stack's naming convention.

**Cannot:** deploy anything. Create, modify or delete any resource. Read any other bucket.
Start a CodeBuild project directly — deliberately omitted, so a run must enter through the
pipeline and the archive under test is the one recorded in the pipeline execution.

**This is deliberately narrower than the reference implementation**
(`launchbridge/internal/infra/credential-vendor`), which attaches `AdministratorAccess`
because CI deploys stacks directly there. Here the privilege that runs the test belongs to
the pipeline's own build role, so this role does not need any.

### But it is still indirect administrator access

Do not read the narrow policy as a containment boundary. The pipeline's `CodeBuildRole`
holds `AdministratorAccess`, and it runs **whatever code this role uploaded**. So:

> Write access to the source key is write access to code that runs as an administrator in
> the target account.

Narrowing this role removes one path to administrator — a stolen CI token cannot call
`iam:CreateUser` directly — not the path. What it buys is a much smaller blast radius for
everything *other* than "run the test": no data exfiltration from other buckets, no
resource deletion, no privilege escalation without going through a pipeline execution that
CloudTrail records. That is worth having, and it is not the same as containment.

## Two conditions are the entire control

```yaml
StringEquals:
  'aws:PrincipalTag/GitLab:Group': <group path>
  'aws:PrincipalTag/GitLab:Project': <project>
```

There is no permissions boundary, no trust expiry and no session cap. A wrong group or
project is the whole security surface.

Two things that read as bugs and are not:

- **`PrincipalTag`, not `RequestTag`.** Hop 1 already attached this metadata as principal
  tags on the caller, derived from the real running job, so by hop 2 it cannot be forged.
  Gating on `RequestTag` would test values the caller supplies with its own request —
  i.e. nothing — and would break vending outright.
- **One statement, carrying the principal, both actions and both conditions together.**
  Splitting `sts:AssumeRole` and `sts:TagSession` into two statements that each repeat the
  condition block is safe only while the repetition stays correct. Any statement that
  permits assumption *without* the conditions fails **open**: it independently allows
  assumption, so the conditions stop constraining anything and the role becomes assumable
  by any project on the instance, with nothing appearing broken. Nothing in this
  repository detects that.

`sts:TagSession` is mandatory. Without it the assumption is denied outright, because the
vendor tags the session during hop 2.

## Install

Deploy `../codepipeline` **first** — this role's policy names that stack's bucket, and the
bucket name is CloudFormation-generated.

```bash
make -C internal/infra/credential-vendor              # help
make -C internal/infra/credential-vendor validate     # template check; free
make -C internal/infra/credential-vendor deploy       # DRY RUN: prints the account
make -C internal/infra/credential-vendor deploy CONFIRM=1
```

`deploy` derives `GitLabGroupName` and `GitLabProjectName` from `git remote get-url
origin`, and reads `SourceBucketName` from the pipeline stack. Override any of them:

```bash
make deploy GITLAB_GROUP=<group/path> GITLAB_PROJECT=<project> \
            SOURCE_BUCKET=<bucket> CONFIRM=1
```

The group path must include **every** subgroup —
`proserve/genaiid/other/candidate-reusable-assets` for this repository. A partial path
fails closed: assumption is denied with nothing indicating the path was wrong.

Then set the `GitLabRoleArn` output as the `AWS_CREDS_TARGET_ROLE` CI/CD variable and
uncomment the variables block in `.gitlab-ci.yml`.

## What silently breaks vending

Each of these deploys cleanly and fails only at assume time, with a denial that does not
name the cause:

- A group path missing a subgroup.
- Renaming the project or moving the group without updating the stack.
- Dropping `sts:TagSession`.
- Changing the hop-2 principal to the hop-1 account.
- Deleting and recreating the role under a generated name — the ARN in the CI/CD variable
  becomes stale. This is why `RoleName` is explicit, and why cfn_nag's `W28` warning about
  it is suppressed rather than fixed: the name is the interface.

`AWS_REGION` matters here, unlike in the reference implementation. That template attaches
only a global managed policy, so region was irrelevant; this one's inline policy names
**regional** ARNs — the pipeline, the build project, the log group — so a stack deployed
into the wrong region grants nothing usable, and it would be discovered only by a CI job
being denied. It is pinned to `us-east-1` with `:=`.

## Verified, and not

**Verified locally:** `aws cloudformation validate-template` passes and reports
`CAPABILITY_NAMED_IAM` (which is what `deploy` passes); cfn-lint 4.x reports nothing;
checkov reports 9 passed / 0 failed; cfn_nag reports 0 failures and one warning (`W28`,
the explicit role name, suppressed with a reason); the group and project derive correctly
from this repository's remote; the dry run stops without acting and correctly refuses when
the pipeline stack does not exist.

**Not verified:** the role has never been deployed, and no CI job has ever assumed it. The
two-hop flow and the principal-tag conditions are transcribed from the reference
implementation, which measured them against its own group and project — they are not
measured here.
