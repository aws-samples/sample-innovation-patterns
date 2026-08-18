# IPA integration tests

A maintainer-only pytest harness that drives the real IPA lifecycle — `/ipa-init` →
`/ipa-compose` → `/ipa-prepare` → `/ipa-deploy` — unattended through the Claude Agent
SDK against a live AWS sandbox, then **asserts the deployed architecture works** rather
than that the run finished.

Nothing here runs in CI on a trigger. A CodePipeline exists
(`internal/infra/codepipeline/`) but is inert (`PollForSourceChanges: false`) and is
started by hand: wiring a trigger would commit the project to paying for a billable run.

```bash
make                # help; creates nothing
make test-offline   # $0, ~5s, no AWS credentials needed
```

## Layout

Shared code in one package, one folder per scenario:

```text
harness/          the shared package — imported as harness.*
  aws.py          the ONE credential and region policy
  fixtures.py     shared session fixtures, loaded as a pytest plugin
  tests/          the free regression suite for the modules above
compose/          scenario: /ipa-init + /ipa-compose, then stop
deploy/           scenario: the full lifecycle
Makefile          the umbrella — delegates to scenarios
```

A scenario is the unit of invocation. That is what keeps the cheap tier cheap to reach: a
composition defect costs about a dollar to find with `compose`, or about fifteen to
rediscover with `deploy`, and the difference only survives if the cheap drive is a
first-class thing you can run and cost on its own rather than a marker expression you
have to remember to narrow.

## Scenarios

| Scenario | Drives | Cost | Leaves standing |
|---|---|---|---|
| `compose` | `/ipa-init`, `/ipa-compose` — stops before `/ipa-prepare` | **$0.94 / 6 min 18 s — measured** | 1 stack: `{ns}-dev-security` (2 IAM roles — free but real) |
| `deploy` | the full lifecycle, all four skills | **unmeasured** | 7 stacks, on purpose |

`deploy`'s cost is **unmeasured, not estimated** — the run has never completed, so no
figure is given rather than a predicted one. A predicted number is the one a reader
trusts without verifying.

```bash
make test-compose          # or: make -C compose test
make test-deploy           # or: make -C deploy test
make -C compose            # that scenario's own help, cost and status
```

Each scenario folder has its own `README.md` stating what it drives, what it costs, what
it leaves behind and how to remove it.

## Current status

| What | Command | Status |
|---|---|---|
| Free suite | `make test-offline` | **green** — 99 tests, ~4.5 s, $0, no credentials |
| Preflight | `make preflight` | **green** where credentials resolve — 9 probes + 1 blocking check |
| `compose` scenario | `make test-compose` | **RED** — `DECISIONS.md` F3 |
| `deploy` scenario | `make test-deploy` | **collects and sets up**; fails at composition for the same cause |

Both scenarios fail for one cause **outside themselves**: `/ipa-compose` generates none
of its eight artifacts, because nothing returns control from `/ipa-security`
(`ipa-compose/SKILL.md:130`). Recorded as `DECISIONS.md` F3. Fixing it is a separate
change — `.claude/skills/**` is public interface.

The `deploy` scenario was, until recently, **uncollectable** rather than merely unrun: it
requested a `deploy_run` fixture that nothing defined, so it failed at *setup* with eight
errors before any probe ran. See `DECISIONS.md` Phase 6.

## Credentials

**Credentials come from the default chain.** No harness AWS call names a profile — not as
a session argument, not as a CLI flag — and no profile name appears as a default in
source. One code path therefore serves both places this runs:

| Where | What answers |
|---|---|
| A workstation | an exported `AWS_PROFILE`, an SSO session, or environment keys |
| CodeBuild | the ECS **container role**, via the container credential provider |

`make preflight`'s first row reports **which** link answered (`env`, `sso`,
`container-role`, `iam-role`), not merely that one did — because a CI build answering from
a stray long-lived key has resolved credentials successfully and is still misconfigured.

`AWS_PROFILE` is still read, for exactly one purpose: it supplies the value the agent
writes into the driven project's `.env`. Four shipped skills stop when that key is absent,
so a run needs a name there — but nothing in this harness needs one to make an AWS call.
`harness.aws.profile_for_env()` is the only reader, and it **raises** when unset rather
than falling back to `default`, because `AWS_PROFILE=default` in `.env` is accepted by
`/ipa-init` and then fails much later inside a generated Makefile with an error naming a
missing profile rather than the configuration step that should have supplied one.

## How to remove what a run leaves standing

```bash
make list-stacks                              # what is standing, across all runs
make teardown-namespace NAMESPACE=<namespace> # remove ONE run
```

Both live on the umbrella rather than in a scenario: a namespace sweep finds any run's
stacks by prefix and belongs to no single scenario.

After a run, a `standing-resources-<namespace>.md` file is written at the **harness
root** — beside this README — naming the namespace, the stacks, and the exact removal
command. It is readable with no AWS credentials configured, because its whole job is to
survive a lost terminal. It is deleted only after a teardown confirms every deletion — a
pointer that outlives a successful teardown teaches you to distrust the next one, which
may be true.

`make teardown-namespace` requires `NAMESPACE`. An empty namespace exits non-zero rather
than being read as "every run".

Teardown also does the three things IPA's own skills refuse to do: drain the versioned
buckets (including every non-current version and delete marker — `aws s3 rm` alone leaves
the bucket un-deletable while making it look empty), empty the ECR registry, and delete
`{ns}-dev-security`.

## Safety properties worth knowing before you run anything

- **Teardown needs two independent opt-ins**: the `teardown` pytest marker *and*
  `IPA_IT_TEARDOWN=1`. One is satisfiable by accident — a pipeline variable applies to
  every phase of every build. Both are set **inline** on the recipe lines that need them
  and nowhere else.
- **Teardown never widens.** It is scoped to one namespace; an unmatched namespace
  selects nothing, and an empty one is refused.
- **`make test-ci` defaults to the cheap scenario.** `SCENARIO ?= compose`, because
  `test-ci` is the name automation reaches for, so its default is a spend decision. An
  unknown `SCENARIO` is refused by name, listing the valid ones.
- **The temp project is preserved whenever stacks are standing** — never on the basis of
  tests passing, and preserved too when the standing check itself errors. It holds `.env`
  and `scripts/*.mk`, the only documented means of teardown, so deleting them while stacks
  stand would remove the means of removing what is still costing money.
- **The one secret this harness generates** — a throwaway Cognito password — is held in
  memory only and redacted from all three sinks that could capture it (the JSONL
  transcript, `DECISIONS.md`, and the standing-resource report). A free test pins the
  filter.
- **The assertions mutate nothing** except a single throwaway user inside the run's own
  Cognito user pool, which the pool's own deletion removes.
- **Each scenario's spend ceiling is set per invocation**, never exported. The two
  ceilings differ threefold, so an ambient one would let the cheap scenario cap an
  expensive run and stop it mid-deployment.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| *(credentials)* | default chain | **No variable.** See [Credentials](#credentials) — an exported `AWS_PROFILE` or SSO session locally, the container role in CodeBuild |
| `AWS_PROFILE` | *(required)* | Read **only** to supply the value written into the driven project's `.env`. Never used to build a session. Raises when unset |
| `IPA_IT_REGION` | `us-east-1` | Pinned; an inherited region would probe an account that is clean only because nothing was ever there |
| `IPA_IT_NAMESPACE` | generated | Pin the run namespace. Validated at source |
| `IPA_IT_STRICT_PREFLIGHT` | unset | Unmet prerequisites **fail** instead of skipping |
| `IPA_IT_TEARDOWN` | unset | Second teardown opt-in |
| `IPA_IT_MAX_BUDGET_USD` | `5` | Spend ceiling for the **compose** scenario |
| `IPA_IT_FULL_MAX_BUDGET_USD` | `15` | Spend ceiling for the **deploy** scenario. Separate on purpose: the two differ threefold, and one shared value set for compose would cap a deploy run at $5 and stop it mid-deployment — indistinguishable from a wedge, and leaving partial infrastructure standing |
| `SCENARIO` | `compose` | Which scenario `make test-ci` runs |
| `VERBOSE` | `1` | `VERBOSE=0` for compact output |

Verbose output is on by default. On a run whose wall clock is deliberately unmeasured,
per-test output is the only way to tell progress from a wedge — and a wedged
twenty-minute billable run with nothing on screen is not recoverable by re-running it.

## Adding a scenario

A scenario is a folder with **five** files. Copy `compose/` and change them:

| File | Holds |
|---|---|
| `Makefile` | `help` (default goal), `test`, `test-ci`, `clean` |
| `pytest.ini` | this scenario's markers, plus the shared-fixtures plugin |
| `conftest.py` | **only** the drive fixture specific to this scenario |
| `README.md` | what it drives, what it costs, what it leaves standing, how to remove it |
| `test_*.py` | the assertions |

Three details are load-bearing rather than stylistic:

1. **`addopts` must include `--import-mode=importlib`.** Under pytest's default `prepend`
   mode, two scenarios each holding a same-named test module collide and one **silently**
   shadows the other — collection succeeds and one module's assertions never run. This is
   the one whose absence does not produce an error.
2. **`addopts` must include `-p harness.fixtures`.** That loads the shared fixtures as a
   plugin. It has to be a plugin rather than an import, because `harness.fixtures` also
   supplies the `pytest_runtest_makereport` hook and pytest collects hooks only from
   `conftest.py` files and plugins.
3. **Every pytest recipe must `cd` to the harness root and use `python -m pytest`**, not
   bare `pytest`. `-m` places the working directory on `sys.path`, which is what makes
   `harness` importable with no build backend and no `pythonpath` entry. The bare console
   script does not, and every module then fails with `ModuleNotFoundError: No module named
   'harness'`.

Then add the scenario to the umbrella's `help` and a `test-<name>` delegating target. The
umbrella's `SCENARIO` guard picks it up automatically — it globs `*/Makefile`.

Set the scenario's spend ceiling **inline** on its recipe lines. Never `export` it: an
ambient ceiling applies to every recipe in the file and to anything else on the same
runner.

## Files

### `harness/` — the shared package

| File | Role |
|---|---|
| `aws.py` | **The one credential and region policy.** `session()` names no profile; `profile_for_env()` answers a different question and never builds a session |
| `fixtures.py` | `credentials`, `resolver`, `namespace`, `transcript`, `temp_project`, the single `_unmet` prerequisite helper, and the preservation rule. Loaded as a plugin |
| `preflight.py` | Nine probes + the Cognito blocking check. Each returns `(ok, detail)` and never raises |
| `workspace.py` | Builds the temp project from the **working tree**, not from a commit |
| `answers.py` | The nine pinned answers; `make_namespace` validates at the point of generation |
| `driver.py` | The SDK session, both answer channels, the per-event transcript, gate markers, both spend ceilings |
| `artifacts.py` | `scripts/*.mk` parsers, kept separate so composition assertions are testable offline |
| `cognito_auth.py` | Mints a real ID token from the run's own pool |
| `standing.py` | `live_stacks` (never raises) and the credential-free pointer |
| `reaper.py` | Removes one run, including the three steps IPA's skills refuse to take |
| `sweep.py` | Cross-run discovery and namespace-scoped teardown |
| `tests/` | The free regression suite for every module above. The **directory** is what marks these free — which is why they need no marker and no name prefix |

### Root

| File | Role |
|---|---|
| `Makefile` | The umbrella. Delegates to scenarios; owns `preflight`, `list-stacks`, `teardown-namespace`, `test-offline` |
| `DECISIONS.md` | **Read this.** Every measured figure and every defect found, with line cites |
