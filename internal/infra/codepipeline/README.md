# Integration-test pipeline

Runs `internal/integration-tests` on CodeBuild instead of a maintainer's laptop, started
on demand. Deployed by hand, per account. Internal maintainer tooling — not shipped.

The pipeline is **inert**: `PollForSourceChanges: false`, so uploading an archive starts
nothing. A billable run happens only when someone asks for one.

## Files

| File | Purpose |
|---|---|
| `integration-test-pipeline.yml` | The stack: bucket, two roles, log group, CodeBuild project, pipeline |
| `Makefile` | Both lifecycles — the stack's (`deploy`/`destroy`) and a run's (`trigger`) |
| `archive.py` | Builds the source zip from the **working tree**, including `.git` |
| `empty_bucket.py` | Empties every object version and delete marker before `delete-stack` |

## Quick start

```bash
make -C internal/infra/codepipeline                    # help; creates nothing
make -C internal/infra/codepipeline validate           # template check; free
make -C internal/infra/codepipeline deploy             # DRY RUN: prints the account
make -C internal/infra/codepipeline deploy CONFIRM=1   # create it
make -C internal/infra/codepipeline trigger CONFIRM=1  # archive+upload+start+watch
make -C internal/infra/codepipeline logs               # tail the build
```

A run's lifecycle is also available piecewise: `archive` (free), `upload` (free, starts
nothing), `start CONFIRM=1`, `watch`.

## Cost

The stack at rest is close to free: an empty bucket, two IAM roles, a pipeline definition
and a log group. Every **execution** costs:

- `BUILD_GENERAL1_LARGE` build minutes, up to the 120-minute `BuildTimeoutMinutes`
  ceiling. The agent-driven run's wall clock is not measured end to end, which is why
  that ceiling exists — a stalled run otherwise burns the whole budget on the most
  expensive compute available, waiting for nothing.
- Model spend, **which scenario you selected decides how much**. See below.
- Everything the test itself deploys — for the `deploy` scenario, seven stacks including
  CloudFront, ECR, two Lambdas, SQS, DynamoDB and S3 — until it is torn down. The
  `compose` scenario deploys one stack of two IAM roles: free, but real.

### Which scenario runs, and what it costs

The `Scenario` parameter selects it, constrained to the scenarios that exist:

| `Scenario` | Drives | Model spend | Deploys |
|---|---|---|---|
| `compose` *(default)* | `/ipa-init`, `/ipa-compose` | **$0.94 — measured** | 1 free-but-real IAM stack |
| `deploy` | the full lifecycle | **unmeasured**, ceiling $15 | 7 billable stacks |

**The default is `compose`, and that is a spend decision rather than a convenience.**
Deploying a pipeline and pressing Start is the first thing anyone does with it, so
whatever the default is gets spent — about $1 here instead of about $15.

`deploy`'s cost is **unmeasured, not estimated**: the run has never completed, so no figure
is given rather than a predicted one.

Each scenario has its own ceiling, and they are separate on purpose:

| Parameter | Bounds | Default |
|---|---|---|
| `MaxBudgetUsd` → `IPA_IT_MAX_BUDGET_USD` | the `compose` drive | `5` |
| `FullMaxBudgetUsd` → `IPA_IT_FULL_MAX_BUDGET_USD` | the `deploy` drive | `15` |

One shared value would be wrong in both directions: sized for `compose`, it caps a deploy
run at $5 and stops it partway through a deployment — indistinguishable from a wedge, and
leaving partial infrastructure standing. `FullMaxBudgetUsd` was previously unreachable,
because `driver.py` hardcoded the full-lifecycle default inside `full_lifecycle_options`.

A mistyped scenario is rejected when this stack's **configuration is applied**
(`AllowedValues`), not deferred to a Makefile error inside a build after LARGE compute has
already been provisioned. The umbrella `Makefile` has its own guard for the same mistake
made by hand; neither covers the other's path.

`post_build` tears down **unconditionally**, so a failed build still cleans up. A build
killed outside its own lifecycle (timeout, `stop-build`) can still leave stacks standing;
`make -C internal/integration-tests list-stacks` is how you find them.

Lower `BuildTimeoutMinutes` once one passing run has been measured. Right now nothing in
this repository knows how long a green run takes.

## The two things most likely to bite

### The archive must contain `.git`

`workspace.py` builds the temp project by copying the **working tree**, and it shells out
to `git ls-files`, `git rev-parse HEAD` and `git status --porcelain` with `check=True`
(`workspace.py:72-101`). An archive without `.git` therefore fails inside a pytest
fixture with a bare `CalledProcessError`, not with a cause.

`archive.py` includes `.git` for exactly this reason, and the buildspec asserts its
presence in the install phase so a wrongly-built archive fails in seconds with an
actionable message. `git archive HEAD` is **not** a substitute: it archives the commit,
so uncommitted edits vanish, and it carries no git metadata at all.

Consequences worth knowing:

- **A dirty tree stays dirty in the archive**, and the build prints a warning naming it.
  That is deliberate — testing an uncommitted skill edit remotely is a real use, and the
  honest failure mode is a loud warning rather than a silently substituted commit.
- **`archive.py` refuses to run from a linked git worktree**, where `.git` is a *file*
  containing a `gitdir:` pointer rather than a directory. Zipping that pointer produces
  an archive whose every git call fails on a path that does not exist in the container.
  Build from the main checkout, or pass `--repo`.
- The archive is around **11 MiB** (694 non-ignored files plus 401 `.git` files, measured).
  Executable bits survive the zip and CodePipeline's unzip — verified against
  `infra/scripts/*.sh`.

The archive excludes git-ignored files, which is what keeps `.env` and the generated
`scripts/*.mk` out. Their absence is load-bearing: it is what keeps `/ipa-init` on its
first-run path, whose prompts the harness can intercept. Only `scripts/test.mk` appears,
because it is tracked — the same exception `workspace.GATING_MAKEFILES` exists to handle.

### The harness names no profile; the GENERATED artifacts do

**The harness authenticates from the default credential chain.** Every AWS call it makes
resolves credentials without naming a profile — see `harness/aws.py`, the single
definition — so inside a build they come from the container's own role. There is nothing
to work around on that side any more.

What still needs a profile *name* is the **driven project**. The agent writes
`AWS_PROFILE` into its `.env` (four shipped skills stop when that key is absent), and the
generated Makefiles then pass `--profile ipa-it` to the AWS CLI. So the buildspec creates
a profile that exists and carries nothing but a region:

```bash
aws configure set region "$IPA_IT_REGION" --profile ipa-it
```

A profile section that defines **no credentials** still resolves them. botocore drops only
`env_provider` when a profile is named explicitly and keeps `container_provider`, which
reads CodeBuild's own credentials. The profile must *exist*, though — `--profile <missing>`
is a hard CLI failure, not a fall-through — which is what that one line creates, and why
creating none at all would break every generated invocation.

The build environment therefore sets `AWS_PROFILE=ipa-it` (it was `IPA_IT_PROFILE`, a
variable the harness no longer reads at all).

**Both of those fall-throughs are inferred from the documented provider order, not
measured** — no run has yet been started from inside CodeBuild. `DECISIONS.md` labels them
as inferred. The install phase's credential check is positioned so that if the inference is
wrong, the build fails there, for free, rather than mid-drive after spending.

## What the buildspec does, and why

- **`uv sync --all-extras`, and `--all-extras` on every later `uv run`.** The Claude
  Agent SDK is behind an optional extra so the offline tier collects without it. A plain
  `uv run` syncs only the default dependencies and would *remove* `claude-agent-sdk`,
  so the extra has to be named every time.
- **`PYTEST='uv run --all-extras python -m pytest'` passed to `make test-ci`.** A
  command-line variable overrides the Makefile's own assignment, so the harness needs no
  edit to run here. It must keep `python -m pytest`: only `-m` places the working directory
  on `sys.path`, which is what makes the `harness` package importable without a build
  backend. With a bare `pytest` console script every test module fails with
  `ModuleNotFoundError: No module named 'harness'`.
- **`SCENARIO="$IPA_IT_SCENARIO"` passed to `make test-ci`.** Selects which scenario folder
  runs. A command-line variable propagates to sub-makes through `MAKEFLAGS`, so it reaches
  the scenario's own Makefile without the umbrella forwarding it.
- **The bundled `claude` binary is verified, and not npm-installed as a fallback.**
  `_find_cli` prefers the bundle over `PATH` (`subprocess_cli.py:249-252`), so an
  `npm install -g` would be ignored while appearing to fix the problem.
- **`python -m harness.preflight --probes-only`** prints the nine-row prerequisite table. It
  reports rather than gates; `test-ci`'s own inline `IPA_IT_STRICT_PREFLIGHT=1` is what
  turns an unmet prerequisite into a failure instead of a silent skip — the difference
  between a build that tested nothing and a build that says so. `--probes-only` skips the
  Cognito blocking check, which deploys a user pool; the run deploys one anyway.
- **The namespace is written to a file, not exported.** Buildspec phases do not share
  shell state, and `post_build` must know the namespace even when the build phase died
  early — which is the case that most needs tearing down. `it` + 10 hex characters is 12
  characters, exactly `answers.NS_MAX_LEN`.
- **`IPA_IT_TEARDOWN` and `IPA_IT_STRICT_PREFLIGHT` are deliberately NOT project
  environment variables.** Both are set inline by the `test-ci` and `teardown-namespace`
  recipes. Declaring either on the project would make it ambient across every phase of
  every build — precisely the "persists invisibly" case the two-part teardown opt-in
  exists to prevent, and it would defeat that mechanism *silently*, because the
  invocation that needs it still works.

## `standard:8.0`, not `7.0`

This repository uses Node 22 (`.gitlab-ci.yml:51`), and Node 22 is not available in
`aws/codebuild/standard:7.0`. The `BuildImage` parameter and the buildspec's
`runtime-versions` block must move together — if the install phase fails with "Unknown
runtime version", that pairing is why. uv downloads its own Python when the image's does
not satisfy `>=3.12`, so the `python: 3.12` pin is belt and uv is braces; the `nodejs`
pin is not recoverable that way.

## Destroying it

```bash
make -C internal/infra/codepipeline destroy             # DRY RUN
make -C internal/infra/codepipeline destroy CONFIRM=1
```

The bucket is **versioned** — mandatory, because CodePipeline's S3 source action refuses
a bucket without versioning. `aws s3 rm --recursive` leaves every noncurrent version and
delete marker behind, and `delete-stack` then fails on a bucket that lists as empty.
`empty_bucket.py` paginates over both `Versions` *and* `DeleteMarkers` and batches deletes
in pages of 1000; a shell one-liner using `--query` piped into `delete-objects` silently
truncates at the first page, producing exactly that misleading failure.

It is stdlib-only and shells out to `aws s3api` rather than importing boto3, so teardown
runs under a bare `python3`. Depending on the harness's uv project would make teardown
fail with an `ImportError` at the moment an operator is trying to delete infrastructure.

`destroy` does **not** touch infrastructure the integration test itself deployed. Check
`make -C internal/integration-tests list-stacks` for that.

## Verified, and not

**Verified locally:** `aws cloudformation validate-template` passes and reports
`CAPABILITY_IAM` (which is what `deploy` passes); cfn-lint 4.x reports nothing; checkov
reports 26 passed / 2 failed (`CKV_AWS_18`, `CKV_AWS_158`); cfn_nag reports 0 failures
and 3 warnings (`W32`, `W84`, `W35`); `archive.py` produces a correct archive and
correctly refuses a worktree; every `CONFIRM`-guarded target's dry run stops without
acting.

**Not verified:** no run of this pipeline has ever executed. The stack has not been
deployed, so the buildspec is unproven end to end — the runtime pairing, the
credential-less profile inside CodeBuild, `dockerd` starting, and whether the harness
completes at all on this compute are all untested. Expect to iterate on the install phase
during the first run. Also note that `make test-compose` is currently **red** on a
maintainer's laptop (`/ipa-compose` generates none of its claimed artifacts), so a first
pipeline run is expected to fail for that reason and not because of anything here.
