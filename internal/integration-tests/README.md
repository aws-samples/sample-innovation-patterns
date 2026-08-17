# IPA integration tests

A maintainer-only pytest harness that drives the real IPA lifecycle — `/ipa-init` →
`/ipa-compose` → `/ipa-prepare` → `/ipa-deploy` — unattended through the Claude Agent
SDK against a live AWS sandbox, then **asserts the deployed architecture works** rather
than that the run finished.

Nothing here runs in CI. `make test-ci` exists and is correct, but no pipeline invokes
it: wiring it would commit the project to paying for a billable run on some trigger.

```bash
make                # help; creates nothing
make test-offline   # $0, ~5s, no AWS credentials needed
```

## Current status

| Tier | Command | Status |
|---|---|---|
| Offline | `make test-offline` | **green** — 100 tests, ~5 s, $0 |
| Preflight | `make preflight` | **green** — 7/9 probes; both blocking unknowns retired |
| Compose | `make test-compose` | **RED** — see `DECISIONS.md` Phase 3, F1–F3 |
| Deploy | `make test` | **blocked** on the compose tier being green |
| Teardown | `make test-teardown` | built; the reaper's path is exercised and works |

`make test` is deliberately gated on `make test-compose` passing first. Composition
defects cost one compose run (~$1) to find; the same defects found from a deploy run
cost a full billable deployment. Two or three compose iterations with a skill fix
between them is the expected path, not the failure path.

## What it costs, measured

Every figure here is **measured on a real run**, never predicted. A predicted number is
the one a reader trusts without verifying.

| Run | Cost | Wall clock | AWS resources |
|---|---|---|---|
| `make test-offline` | $0 | 4.5 s | none |
| `make preflight` | pennies | ~4 min | 2 stacks under `itprobe`, **both deleted by the run** |
| `make test-compose` | **$0.94** | **6 min 18 s** | 1 security stack (IAM roles — free but real) |
| `make test` | not yet measured | not yet measured | **seven stacks, left standing** |

`make test` has not been run, so its cost is unrecorded rather than estimated. For
scale only, and from a different codebase: the reference harness measured a comparable
billable path at $3.38 over 24 minutes for five stacks.

## What `make test` creates, and that it is LEFT STANDING

A passing `make test` deploys **seven CloudFormation stacks** under a per-run namespace
and **leaves them running on purpose**, so you can open the app in a browser and
confirm by eye what the assertions claim:

| Stack | What it holds |
|---|---|
| `{ns}-dev-logs` | S3 log bucket (versioned) |
| `{ns}-dev-ecr` | ECR repository holding a container image |
| `{ns}-dev-cognito` | Cognito user pool + hosted-UI domain |
| `{ns}-dev-security` | IAM execution roles |
| `{ns}-dev-queue` | SQS queue + DLQ + worker Lambda + DynamoDB |
| `{ns}-dev-backend` | Lambda (container) + API Gateway v2 + DynamoDB |
| `{ns}-dev-frontend` | S3 site bucket (versioned) + CloudFront distribution |

**These cost money for as long as they exist.** CloudFront and the two Lambdas are the
meaningful line items.

## How to remove it

```bash
make list-stacks                              # what is standing, across all runs
make teardown-namespace NAMESPACE=<namespace> # remove ONE run
```

After a run, a `standing-resources-<namespace>.md` file is written **beside this
README** naming the namespace, the stacks, and the exact removal command. It is
readable with no AWS credentials configured, because its whole job is to survive a lost
terminal. It is deleted only after a teardown confirms every deletion — a pointer that
outlives a successful teardown teaches you to distrust the next one, which may be true.

`make teardown-namespace` requires `NAMESPACE`. An empty namespace exits non-zero
rather than being read as "every run".

Teardown also does the three things IPA's own skills refuse to do: drain the versioned
buckets (including every non-current version and delete marker — `aws s3 rm` alone
leaves the bucket un-deletable while making it look empty), empty the ECR registry, and
delete `{ns}-dev-security`.

## Safety properties worth knowing before you run anything

- **Teardown needs two independent opt-ins**: the `teardown` pytest marker *and*
  `IPA_IT_TEARDOWN=1`. One is satisfiable by accident — a pipeline variable applies to
  every phase of every build.
- **Teardown never widens.** It is scoped to one namespace; an unmatched namespace
  selects nothing, and an empty one is refused.
- **The temp project is preserved whenever stacks are standing** — never on the basis
  of tests passing, and preserved too when the standing check itself errors. It holds
  `.env` and `scripts/*.mk`, the only documented means of teardown, so deleting them
  while stacks stand would remove the means of removing what is still costing money.
- **The one secret this harness generates** — a throwaway Cognito password — is held
  in memory only and redacted from all three sinks that could capture it (the JSONL
  transcript, `DECISIONS.md`, and the standing-resource report). An offline test pins
  the filter.
- **The assertions mutate nothing** except a single throwaway user inside the run's own
  Cognito user pool, which the pool's own deletion removes.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `IPA_IT_PROFILE` | `peterpyu+code-evaluation-Admin` | AWS profile |
| `IPA_IT_REGION` | `us-east-1` | Pinned; the agent's bare `aws` calls carry no `--region` |
| `IPA_IT_NAMESPACE` | generated | Pin the run namespace. Validated at source |
| `IPA_IT_STRICT_PREFLIGHT` | unset | Unmet prerequisites **fail** instead of skipping |
| `IPA_IT_TEARDOWN` | unset | Second teardown opt-in |
| `VERBOSE` | `1` | `VERBOSE=0` for compact output |
| `IPA_IT_MAX_BUDGET_USD` | `5` | Spend ceiling for the compose tier |

Verbose output is on by default. On a run whose wall clock is deliberately unmeasured,
per-test output is the only way to tell progress from a wedge — and a wedged
twenty-minute billable run with nothing on screen is not recoverable by re-running it.

## Files

| File | Role |
|---|---|
| `preflight.py` | Nine probes + the Cognito blocking check. Each returns `(ok, detail)` and never raises |
| `workspace.py` | Builds the temp project from the **working tree**, not from a commit |
| `answers.py` | The nine pinned answers; `make_namespace` validates at the point of generation |
| `driver.py` | The SDK session, both answer channels, the per-event transcript, gate markers |
| `artifacts.py` | `scripts/*.mk` parsers, kept separate so composition assertions are testable offline |
| `cognito_auth.py` | Mints a real ID token from the run's own pool |
| `standing.py` | `live_stacks` (never raises) and the credential-free pointer |
| `reaper.py` | Removes one run, including the three steps IPA's skills refuse to take |
| `sweep.py` | Cross-run discovery and namespace-scoped teardown |
| `DECISIONS.md` | **Read this.** Every measured figure and every defect found, with line cites |
