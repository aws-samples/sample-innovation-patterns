# internal/infra/

Two CloudFormation stacks that let the integration-test harness run somewhere other
than a maintainer's laptop. **Both are installed by hand, per account.** No CI job
deploys either, and nothing in this repository deploys them automatically.

Once both exist, CI can *start* a run — the two manual `integration-test:*` jobs in
`.gitlab-ci.yml`. Starting is all it can do: the jobs call these same Makefile targets
through a role that cannot create, modify or delete anything.

| Directory | What it creates | Needs |
|---|---|---|
| `codepipeline/` | A versioned S3 bucket, a narrow pipeline role, a build role with `AdministratorAccess`, one CodeBuild project, one pipeline | `CAPABILITY_IAM` |
| `credential-vendor/` | One IAM role, assumable only by the code.aws.dev credential vendor, that can start a run of the above and read its result | `CAPABILITY_NAMED_IAM` |

Neither is shipped. `internal/` is excluded from the public GitHub mirror, and unlike
`internal/release/templates/` these are **not** public interface — see
`internal/README.md` for that distinction.

## Why these are here and not under `infra/cfn/`

`infra/cfn/**` is customer-facing: those templates are composed by `/ipa-compose` and
delivered to users, so their parameter names, outputs and logical IDs are breaking-change
surface. `infra/cfn/codepipeline/codepipeline.yml` in particular is a **customer
application** pipeline — it runs the generated `scripts/*.mk` targets for a deployed app.
It is not this, and pointing the harness's own CI at it would couple maintainer tooling
to a shipped deliverable: a change made for the harness would become a breaking change
for every customer.

That template is untouched by this directory and remains in use.

## Install order

`credential-vendor` references the pipeline's bucket and pipeline name, and the bucket
name is CloudFormation-generated, so it cannot be known before the pipeline exists.

```bash
# 1. The pipeline. Dry run first — without CONFIRM=1 this prints the resolved
#    account and stops.
make -C internal/infra/codepipeline deploy
make -C internal/infra/codepipeline deploy CONFIRM=1

# 2. Run the test once by hand, before wiring anything to it.
make -C internal/infra/codepipeline trigger CONFIRM=1

# 3. Only if GitLab CI should be able to start runs. Reads the two values it
#    needs from the pipeline stack's outputs automatically.
make -C internal/infra/credential-vendor deploy
make -C internal/infra/credential-vendor deploy CONFIRM=1
```

Step 3 is genuinely optional, and worth skipping until step 2 has passed at least once.
The pipeline is fully usable by hand; the role only exists to let a CI job do what
`make trigger` does.

After step 3, paste the role ARN into `.gitlab-ci.yml`'s `.integration-test-base` (a
job-level variable — `credential-vendor/README.md` says why not a project one) and the
`integration-test:start` job becomes a button in the GitLab UI.

## State, as of 2026-09-08

| | |
|---|---|
| `codepipeline` stack | **deployed** in 369530416671 / `us-east-1`, created 2026-08-18 |
| That stack's template | **behind this repository** — deployed before `Scenario` and `FullMaxBudgetUsd` existed, so re-deploy before the next run |
| `credential-vendor` stack | **deployed** 2026-09-08 as `InnovationPatternsGitLabCI` |
| Vending, and `integration-test:start` | **work** — first run started from GitLab CI on 2026-09-08 uploaded the archive and started the pipeline |
| Runs | **two, both failed.** 2026-08-18 at the Source stage (`start` called with nothing uploaded). 2026-09-08 in `BUILD`, on two `/ipa-compose` assertions — 16 of 18 tests passed, every buildspec phase worked, and `post_build` tore its namespace down. See `codepipeline/README.md` for what that measured |
| Left over from an earlier manual run | **seven billable stacks** under namespace `it1e5bd7c3f3`, standing since 2026-08-19. `make -C internal/integration-tests teardown-namespace NAMESPACE=it1e5bd7c3f3` |

## Conventions both directories share

- **A bare `make` prints help and creates nothing.**
- **Every target that changes an account or spends money needs `CONFIRM=1`.** Without
  it, the target prints what it would do — including the account resolved from
  `sts:get-caller-identity`, not from a variable — and stops. `make deploy` with no
  `CONFIRM` is the dry run.
- **`AWS_REGION` is pinned to `us-east-1` with `:=`, not `?=`.** `?=` yields to an
  exported variable, and a shell exporting `AWS_REGION=us-west-2` silently captured it —
  `make help` printed one region while the Makefile said another. A command-line
  `make AWS_REGION=<r> <target>` still wins.
- **`AWS_PROFILE` defaults only if that profile actually exists** on the machine, because
  `--profile <missing>` is a hard failure on a host using an instance role, not a
  fall-through to ambient credentials.
- **Destructive and dry-run logic lives in ONE shell block per target.** `exit 0` leaves
  only its own recipe line's subshell, so a guard on its own line does not stop the
  target. That bug was written and caught here: a `trigger` dry run printed "nothing was
  done" and then started a billable run.

## Which account?

**Settled by deployment: 369530416671 (`vincilb+ip-dev-Admin`).** Both stacks live there,
and the credential-vendor role's trust policy names this repository's GitLab group, so a CI
run cannot land anywhere else. What remains is a *disagreement inside the harness*, not an
open choice — `preflight.py` still names an evaluation sandbox, which matters only for the
manual runs recorded in `DECISIONS.md` and for anyone reading those figures as if they came
from this account.

The three values, for the record:

| Source | Account / profile |
|---|---|
| Both Makefiles here | `vincilb+ip-dev-Admin` (369530416671) |
| `internal/integration-tests/preflight.py:56` | `peterpyu+code-evaluation-Admin` — where every manual run was measured |
| This repository's `.env` | `vincilb+ip-dev-Admin` |

Inside the build there is no profile at all: the buildspec creates a credential-less
`ipa-it` profile that resolves the container's own credentials, so the harness's
requirement for a *named* profile is satisfied without one being configured. The
disagreement only matters for the hand-run targets, and for reading the measured costs in
`DECISIONS.md` — those figures come from the sandbox row, not from the account the stacks
are now in.

## Security posture, stated once

`codepipeline/`'s `CodeBuildRole` holds `AdministratorAccess`, because the run it
executes deploys and then deletes arbitrary infrastructure. Therefore:

> `s3:PutObject` on the source key, plus `codepipeline:StartPipelineExecution`, are the
> **entire** control on executing arbitrary code as an administrator in the target
> account.

`credential-vendor/` grants exactly those two things and nothing else — deliberately not
`AdministratorAccess`, unlike the reference implementation it is modelled on. That
removes one path to administrator, not the path: whatever a CI job uploads still runs
under the build role. Read `credential-vendor/README.md` before treating the narrow role
as a containment boundary.

Unlike the reference's repository, `internal/**` here is **not** exempt from ASH. Both
templates are scanned, and `.ash/ash.yaml` suppresses ten findings against
`internal/infra/**` by path, each with a reason. The suppressed set was measured
(checkov, cfn_nag, cfn-lint) rather than anticipated; KICS was not run locally and may
add names of its own.
