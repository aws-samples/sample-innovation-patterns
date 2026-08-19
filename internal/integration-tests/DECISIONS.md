# IPA Integration Tests — Decisions and Measurements

Findings that would otherwise live only in a git-ignored temp project, and be lost
with it. Every figure here is **measured**, never predicted.

---

## Target

| | |
|---|---|
| **Account** | `450282238889` |
| **Caller** | `arn:aws:sts::450282238889:assumed-role/Admin/vincilb-Isengard` |
| **Credentials** | The **default chain** — no profile is named in source. See Phase 6, D6.2. (Runs through 2026-08-17 recorded below used a named `IPA_IT_PROFILE`, since retired.) |
| **Region** | `us-east-1` |
| **Account type** | Isengard evaluation sandbox (`code-evaluation`), not production |

The region is pinned rather than inherited. This shell exports
`AWS_REGION=us-west-2`, and `/ipa-deploy` Step 1.5's `describe-stacks` is a bare
`aws` call carrying no `--region` — so an inherited region sends that gate to the
wrong region and hard-stops on a stack that exists.

---

## Phase 1 — Preflight (run 2026-08-17)

`python -m preflight` — nine probes, cheapest-first, no short-circuit. Plus one
blocking check (`cognito_token`) held out of the probe table because it deploys a
user pool, and `conftest.py` must not deploy one while deciding whether to skip.

| Probe | Outcome | Detail (verbatim where negative) |
|---|---|---|
| `aws_profile_resolvable` | **PASS** | profile `peterpyu+code-evaluation-Admin` resolvable in `us-east-1` |
| `sts_caller_identity` | **PASS** | `account=450282238889 arn=arn:aws:sts::450282238889:assumed-role/Admin/vincilb-Isengard` |
| `claude_agent_sdk_importable` | **FAIL** | `optional dependency not installed: No module named 'claude_agent_sdk'` |
| `npm_present` | **PASS** | `npm 11.17.0` |
| `uv_present` | **PASS** | `uv 0.12.3 (Homebrew 2026-08-07 aarch64-apple-darwin)` |
| `docker_daemon` | **PASS** | `docker server 29.6.2` |
| `bedrock_worker_model` | **FAIL** | `worker model: MODEL NOT FOUND/INVALID -- Access denied. This Model is marked by provider as Legacy and you have not been actively using the model in the last 30 days. Please upgrade to an active model on Amazon Bedrock` |
| `bedrock_driver_model` | **PASS** | `driver model: invoke ok (us.anthropic.claude-sonnet-4-20250514-v1:0)` |
| `iam_create_role` | **PASS** | two named roles created and deleted under `itprobe` with `ReadOnlyAccess` and `CAPABILITY_NAMED_IAM` |
| `cognito_token` *(blocking check)* | **PASS** | `IdToken aud == UserPoolClientId (5836p9aro9uv2pt6ma57f6mla5); itprobe-dev-cognito deleted; domain prefix itprobe-dev-62417329 released` |

**7/9 probes passed; both blocking unknowns are retired.**

### Both blocking unknowns are retired

The two unknowns that could have made this feature impossible both resolved
favourably, and both cost cents rather than a billable run:

1. **`iam:CreateRole` with `CAPABILITY_NAMED_IAM` works in this account.** A
   two-role stack mirroring `/ipa-security`'s generated `iam.yml` — explicit
   `RoleName`s, one role trusting the account root and one trusting
   `codebuild.amazonaws.com`, each attaching one managed-policy ARN — deployed and
   deleted cleanly. **Route A for the security-stack deadlock is viable.**
2. **`AdvancedSecurityMode: ENFORCED` does not block programmatic
   `InitiateAuth`.** The project's own `infra/cfn/cognito/cognito.yml`, deployed
   unchanged, returned an `IdToken` to `USER_PASSWORD_AUTH` with no adaptive-auth
   challenge — and the token's `aud` claim equals the `UserPoolClientId`, so the
   API Gateway audience check will pass in Phase 4. This mattered because the
   natural fallback is unavailable: `ALLOW_ADMIN_USER_PASSWORD_AUTH` is absent
   from the pool client's `ExplicitAuthFlows`, so `AdminInitiateAuth` would have
   required a change to a customer-facing template.

### The two negative outcomes

**`claude_agent_sdk_importable` — expected, not a defect.** Phase 1 declares only
`boto3`; the SDK arrives behind an optional extra in Phase 2. A negative outcome
here reads as a missing optional dependency, which is its designed behaviour on a
machine that has not installed the extra.

**`bedrock_worker_model` — a real finding, and it corroborates HITL default Q3.A.**
`anthropic.claude-3-haiku-20240307-v1:0` is **not invocable in this account**: the
provider has marked it Legacy and access is denied for not having been used in the
last 30 days. Consequences:

- The queue assertion in Phase 4 must **not** require a job to reach `COMPLETED`.
  It stops at "no longer `PENDING`" and **a `FAILED` job passes** — which was
  chosen on reasoning before this run and is now backed by a measurement: the
  model the worker calls cannot be invoked here at all.
- The plan's alternative Q3.C — fail on `FAILED` only when the Bedrock probe
  passed — would have made the suite skip that assertion entirely in this account,
  which is a weaker signal than reporting the terminal status.
- Whoever wants a `COMPLETED` job must either request access to an active model or
  point `IPA_IT_WORKER_MODEL` at one. Recorded rather than fixed, because the
  worker model is `app-lib`'s choice and changing it is a separate change.

### Decisions that would otherwise read as oversights

**`ReadOnlyAccess`, not `PowerUserAccess`** (HITL default K1.A). `/ipa-deploy`
Step 1.5 checks only that `{ns}-{env}-security` reports `CREATE_COMPLETE` or
`UPDATE_COMPLETE`; it never assumes either role, and `APP_BUILDER_ROLE_ARN`
appears zero times in `MAKEFILE_TEMPLATES.md`. So `ReadOnlyAccess` satisfies that
gate identically with a strictly smaller IAM footprint, and it removes the tension
with `.context/README.md`'s "no wildcard IAM resource ARNs" constraint that
`PowerUserAccess` would introduce — every AWS-managed policy is wildcard-scoped.

The cost, stated so it is not lost: the run no longer exercises the option a real
builder most likely picks. If `/ipa-security` ever starts validating that the
chosen policy actually grants deploy permissions, this answer breaks — nothing in
its Step 3a suggests it does. One constant (`PROBE_MANAGED_POLICY_ARN`) reverses
the decision.

**The JWT is decoded without verifying its signature**, deliberately and narrowly.
The token was minted seconds earlier by the probe itself against the pool it had
just deployed, and the only claim read is compared to a value from that same
deployment. Verifying would add a JWKS fetch and a crypto dependency to establish
something already known. This is **not** a pattern for anything that trusts an
inbound token, and the docstring on `_jwt_payload` says so.

### What the probe run creates, and that it cleans up

Two stacks under namespace `itprobe` in `us-east-1`, both deleted by the run:

- `itprobe-dev-security` — two IAM roles (free)
- `itprobe-dev-cognito` — one user pool with a hosted-UI domain (free at this scale)

Teardown runs in a `finally` path, so a probe that fails midway still cleans up.
Verified afterwards:

```
$ aws cloudformation list-stacks --region us-east-1 \
    --query "StackSummaries[?starts_with(StackName,'itprobe') && StackStatus != 'DELETE_COMPLETE']"
(empty)
$ aws iam list-roles --query "Roles[?starts_with(RoleName,'itprobe')].RoleName"
(empty)
```

The globally-unique Cognito domain prefix `itprobe-dev-62417329` was confirmed
released. A leak there would make the probe non-repeatable, with a second run
failing on a name the first run took — an error that names a name rather than a
cause.

### The generated password

Generated with `secrets`, built by character class rather than by rejection
sampling (all four classes are required by `cognito.yml`'s password policy, and
rejection sampling can fail intermittently), and **held in memory only**. It is
written to no file — not this one, not a transcript, not a report. Phase 4 adds the
redaction filter for the sinks that will exist then; Phase 1's obligation is simply
not to write it anywhere.

### Notes on the probe design

- **The Docker probe reads `{{.ServerVersion}}`, not the exit code.** `docker
  info` exits 0 with a partial payload when the daemon is down, so an exit-code
  check reports a working daemon that is not there — and the failure resurfaces
  twenty minutes later inside `build-rest-lambda`. Empty output is treated as a
  stopped daemon, which is the safe direction: a format change yields a false
  negative, never a false positive that costs a container build.
- **The runner does not short-circuit.** Stopping at the first negative outcome
  would have hidden `bedrock_worker_model` behind `claude_agent_sdk_importable`,
  turning one round of environment repair into two — and nothing is saved, because
  the expensive probes are last.
- **`import preflight` runs no probe and creates no AWS resource.** Verified.

---

## Phase 2 — Offline harness (run 2026-08-17)

`make test-offline`: **86 tests, all passing, 4.5 s, with no AWS credentials
required.** ASH/bandit: **zero findings at MEDIUM or above** for the first-party
modules.

### Two premises in the plan were wrong, and both were found here rather than in a paid run

**1. `scripts/test.mk` is TRACKED, so the temp project is not free of generated
Makefiles.** The plan asserted that "`scripts/*.mk` is git-ignored
(`scripts/.gitignore:2`) — so the copy starts with neither". `scripts/.gitignore`
does list `*.mk`, but **git's ignore rules do not apply to a file that is already
tracked**, and `git ls-files scripts/` returns `scripts/test.mk`. A blanket
`scripts/*.mk` assertion therefore fails on every healthy build of this repository.

Resolved by narrowing the pristine check to the Makefiles that actually **gate a
skill branch** (`workspace.GATING_MAKEFILES`):

- `.env` is what sends `/ipa-init` into its re-initialization branch, whose
  plain-text *"Which values would you like to change?"* no hook can intercept.
- `scripts/deploy.mk` is what `/ipa-compose` Step 0.3 checks to select its
  idempotent-refresh mode (`ipa-compose/SKILL.md:57`).

`test.mk` gates neither, so its presence changes no skill's path. The narrowing is
correct rather than merely convenient, and two offline tests pin it: one asserts a
tracked `test.mk` is tolerated, one asserts `deploy.mk` is refused.

**2. `deploy:` and `teardown:` prerequisites never share a name**, so the
"exact reverse" check cannot compare them raw. `MAKEFILE_TEMPLATES.md:54` generates
`deploy: deploy-{suffix1} … deploy-{suffixN}` and `:162` generates
`teardown: teardown-{suffixN} … teardown-{suffix1}`. A raw comparison reports
**every healthy artifact as misordered** — a false positive that would have been
recorded as a skill defect in Phase 3 and "fixed" in a skill that was correct.

Resolved by comparing tier suffixes (`artifacts._suffixes`). An offline test asserts
both that the suffix comparison passes on a healthy fixture and that the raw
comparison would *not* — so the fix cannot silently regress.

### Notes on the implementation

- **The version purge is the normal path, not a fallback.** `aws s3 rm --recursive`
  runs first because it is fast, then a paginated `list-object-versions` /
  `delete-objects` sweep drains both `Versions` and `DeleteMarkers`
  unconditionally. `empty_bucket` treats the **purge** as authoritative, because
  `s3 rm` succeeding tells you nothing about whether `DeleteBucket` will: on a
  versioned bucket it leaves the bucket un-deletable while making it look empty. A
  test asserts that a **failed** listing does not report `emptied`.
- **Nothing ties with `LOGS_RANK`.** `logs` is deliberately absent from
  `TIER_ORDER`; appending it is what creates a tie with an unknown tier, and under
  a stable sort a tie keeps input order. Tests assert no two distinct tiers share
  the rank, and that `logs` sorts last for **every permutation** of an input
  listing.
- **An empty namespace is refused at the deleting boundary**, not interpreted as
  "every run". `select_namespaces` passes a listing through when given nothing —
  which is right for `list` — so the refusal lives in `cmd_teardown` and in the
  `teardown-namespace` target, and both are tested to delete nothing.
- **`make_namespace(None)` generates; `make_namespace("")` raises.** An empty
  string is invalid, not absent — otherwise a caller that meant to inject a
  namespace would silently get a different one than it recorded. Callers reading an
  environment variable pass `os.environ.get(...) or None`.
- **The VERBOSE `filter-out` form is verified, not assumed.** `make -n VERBOSE=0
  test-offline` emits `-q`; `VERBOSE=1` and unset both emit `-vv -s -rs
  --log-cli-level=INFO`. The `$(if $(VERBOSE),…)` form would have turned `VERBOSE=0`
  **on**, because Make's `$(if)` branches on non-emptiness rather than truth.
- **`B404`, `B603` and `B607` are suppressed inline in source *and* by path in
  `.ash/ash.yaml`.** Measured with bandit against the first-party modules, only
  `B101` remains and MEDIUM+ is zero — the inline `# nosec` markers already cover
  the subprocess rules. The path suppressions are added anyway because ASH runs its
  own bandit configuration, which need not honour inline markers. Every subprocess
  call uses an argv list with `shell=False`, which is what makes the `B603`
  justification true rather than merely written.
- **`output.py` was cut** (HITL default K2.A). The transcript and the
  standing-resource report already survive a lost terminal, and adopting it would
  also adopt a cross-suite coupling the reference documented as a cost.

## Phase 3 — Compose-only drive (run 2026-08-17)

> **Phase 3 is RED. Phase 4's billable run is BLOCKED** (HITL default S1.A: Phase 4
> is gated on Phase 3 being *green*, not on Phase 3 having run once). Three findings
> below, two of which are defects in shipped skills and must be fixed in their own
> changes with bumping commit types.

### Measured, not predicted

| | |
|---|---|
| **Cost** | **$0.9417** |
| **Turns** | **30** (ceiling 300) |
| **Wall clock** | **377.8 s** (6 min 18 s) |
| Stopped by a ceiling? | **No** — the agent ended on its own |
| Namespace | `itf7676bc5d5` |
| Temp project | `201edc74a788-dirty`, 690 files |
| Gates seen | `compose:overwrite`, `security:deploy` |
| Result | 5 passed, 10 failed, 3 errors |

Well under the $5 ceiling (Q2.A), so the ceiling is not the constraint. A first
harness-bug iteration cost a further ~$0 (aborted after 10 s on a `TypeError`).

### What passed — the answer path works, through one channel only

- **`APP_NAMESPACE` == `itf7676bc5d5`.** The single discriminator. The pinned
  namespace reached `.env` exactly.
- `AWS_PROFILE` is the real profile name, **not** `Skip` — so defect 6 did not fire,
  as predicted.
- `AWS_REGION=us-east-1`, `APP_ENV=dev`, `APP_IAC=cloudformation` all pinned.
- No unexpected stack was deployed; the stop-after-compose instruction held.

### F1 — `AskUserQuestion` was NEVER invoked, so the resolver never fired

**The entire hook/resolver mechanism was bypassed.** Zero `ask_user_question` events
in a 1,353-event transcript. The agent read `/ipa-init`'s prose, saw the pinned values
in the appended system prompt, and wrote `.env` itself — verbatim:

> *"Since this is an automated integration test, I'll configure the project with the
> required values"*

This is a **finding about the harness's model, not a skill defect**, and it inverts a
plan premise. The plan treated the `PreToolUse` hook as the answer channel and the
system-prompt namespace as a belt-and-braces second channel; in fact the system prompt
was the *only* channel that operated, and the hook was never reached.

Consequences:

- `test_the_answer_channel_is_recorded` fails, correctly — it asserts a batch was
  answered, and none was.
- **Answers 6–9 of the nine-entry table never applied at all**, because those
  questions are asked by `/ipa-compose` Step 1.5 and `/ipa-security`, which the agent
  also answered itself. See F2 for what it chose instead.
- The measured reference behaviour (`iac_compose/FINDINGS.md` F2 — that `PreToolUse`
  answers and `can_use_tool` does not) is **neither confirmed nor refuted here**,
  because neither path was exercised. Both registrations stay: the `can_use_tool`
  tripwire is now *more* justified, not less, since the channel that fires is
  evidently not fixed.

The fix belongs in the harness, not in a skill: either the system prompt must stop
pre-supplying values so the questions are actually asked, or the harness must accept
that the prompt is the channel and assert on `.env` rather than on channel use. That
is a Phase 3 re-run, not a skill change.

### F2 — the agent selected Route C, not Route A, so `ReadOnlyAccess` never applied

Because no question was asked, nothing answered `/ipa-security` with `"Managed
policy"` → `ReadOnlyAccess` → `"Yes, deploy"`. The agent took the **Recommended**
option instead — *Innovation Builder Stack* (`ipa-security/SKILL.md:109`) — and
deployed, verbatim:

```
Path               Innovation Builder Stack
Builder Role       itf7676bc5d5-dev-builder
CodeBuild Role     itf7676bc5d5-dev-codebuild
SageMaker Role     itf7676bc5d5-dev-sagemaker
EC2 Builder Role   itf7676bc5d5-dev-ec2-builder
Security Stack     itf7676bc5d5-dev-security   (IAM roles + permissions boundary + policies)
```

**Four roles, a permissions boundary and a 47-service policy** — where Route A with
HITL default K1.A intended two roles with `ReadOnlyAccess`. So the smallest-footprint
decision recorded in Phase 1 was silently not the one exercised, and the constraint
tension that K1.A was chosen to remove was reintroduced by the agent's own default.

Still free, still real, and it **was deleted** — see teardown below.

### F3 — `/ipa-compose` generated ZERO of its eight artifacts

The most consequential finding. After delegating to `/ipa-security` and reporting
success, the run **ended without returning to `/ipa-compose`'s artifact generation**.
`scripts/` afterwards held only what the repository copy already contained:

```
.gitignore  INSTALL-RUNBOOK.md  lint/  test.mk
```

None of `prepare.mk`, `deploy.mk`, `build.mk`, `post-deploy.mk`, `env.mk`,
`release.mk`, `SECURITY-DISPOSITION.md`. `/ipa-compose` claims all eight
(`ipa-compose/SKILL.md:266-274`).

This answers research gap 9 — *"whether `/ipa-compose` generates all eight artifacts
on a real run is unverified"* — with **no**, on this run.

The proximate cause is a control-flow gap: `/ipa-compose` Step 1.5 delegates to
`/ipa-security` and instructs *"On success … Proceed to Step 2"*
(`ipa-compose/SKILL.md:130`), but nothing in the delegated skill returns control, and
`/ipa-security`'s own completion report reads as terminal. The agent treated the
security report as the end of the task. **This is a defect in a public interface**
(`.claude/skills/ipa-compose/SKILL.md`) and must be fixed in its own change with a
bumping commit type — not here.

Because composition was never reached, the assertions that exist to catch defects 1–5
could not run at all. That is the **cheap direction** and the recorded expectation:
defects 1, 2 and 3 are detected by *reaching composition at all*. `test.mk` being the
only `*.mk` present is also why Phase 2's tracked-`test.mk` finding mattered — a
blanket `scripts/*.mk` pristine check would have masked this as a copy problem.

### A false-positive in the gate scanner, worth recording

`compose:overwrite` was recorded as a gate hit, but the matching text was
`/ipa-compose`'s **own SKILL.md prose**, echoed into assistant output when the skill
was loaded — not a question the agent asked. The scanner matches markers against all
assistant text, including echoed skill content. Harmless here (the record is
verbatim, so the false positive is visible on inspection) but it means a gate count is
not a gate-crossing count.

### Teardown worked, end to end

The harness's own path removed everything, first try:

```
$ make teardown-namespace NAMESPACE=itf7676bc5d5
Tearing down itf7676bc5d5 (1 stack(s))
  ok   itf7676bc5d5-dev-security
  removed standing-resources pointer for itf7676bc5d5
```

Verified afterwards: no stack under any `it*` namespace, and no `itf7676*` IAM role.
The standing-resource report fired through all three channels during the run
(file, print, `UserWarning`), and the pointer was removed **only** after confirmed
deletion — the reference's F5 behaviour, working as specified.

### The preservation rule proved itself

The temp project was **preserved** at session teardown because the security stack was
standing — not because tests failed, and not deleted because tests failed. That is the
rule working in the direction that matters: `.env` and the security stack's identifiers
were still the only record of what had been created.

## Phase 4 — Full lifecycle and live assertions (built; run BLOCKED)

**Every module and assertion is written and collects. The billable run has not been
executed, because Phase 3 is red** and HITL default S1.A gates Phase 4 on Phase 3
being *green*, not on Phase 3 having run once. Running it now would spend a full
deployment to rediscover F3 — the exact trade the gate exists to prevent.

Built and verified as far as it can be without deploying:

- `cognito_auth.py` — throwaway user, permanent password by character class,
  `USER_PASSWORD_AUTH`, returns the **ID token** and asserts `aud == client_id`. Its
  mechanism is already proven: Phase 1's preflight ran exactly this path against a real
  pool and got a token.
- `test_deploy.py` — 20 assertions across seven-stack health, the served SPA and its
  `config.js`, the exactly-401 anonymous check, both authenticated checks, the direct
  `lambda:Invoke` container probe, the queue round trip, the DLQ, the queue outputs and
  the event-source mapping.
- `test_teardown.py` — verify-live-then-reap, both removal directions, and the pointer
  check, behind both opt-ins.
- **The redaction filter is complete and pinned by offline tests** (11 of them):
  a registered secret is replaced in the transcript, nested payloads included; an
  *un*registered value is **not** redacted, so over-redaction cannot silently destroy
  the verbatim gate text the transcript exists to preserve; the generated password
  satisfies all four required character classes across 200 generations; and every gate
  marker is asserted lowercase, since the scanner lowercases the haystack and an
  upper-case marker would never match.

### The one write the assertions make — recorded as a narrowed exception

**The assertions mutate nothing except a single throwaway user inside the run's own
Cognito user pool.** The pool's own deletion removes it, so there is no separate cleanup
obligation. Recorded explicitly because "the assertions are read-only" is the kind of
claim that is either exactly true or quietly false, and the difference matters to
whoever audits the account afterwards.

### Unrecorded because unmeasured

Cost, wall clock and turns for `make test` are **absent, not estimated**. The reference
harness's $3.38 / 24 minutes for five stacks is from a different codebase and is quoted
in `README.md` as scale only, never as a prediction for this one.

## Phase 5 — CI seams (built and verified; nothing wired)

Both seams work, and neither is invoked by anything.

**`IPA_IT_STRICT_PREFLIGHT` measured both ways** against an unresolvable profile:

| Mode | Result |
|---|---|
| unset | `45 skipped in 0.05s` |
| `=1` | `45 errors in 0.21s`, nothing created |

Fails fast for free because `preflight.py`'s probes are ordered cheapest-first, so an
unresolvable profile is probe one. This is the seam that matters most: a skip is right on
a laptop and catastrophic in a pipeline, where a build that skips every billable test
**exits 0 having tested nothing** — a green result proving only that the runner started.

**`IPA_IT_NAMESPACE` closed a live gap, not just added a seam.** Measured:

```
IPA_IT_NAMESPACE=itvalid99  -> resolver namespace: itvalid99
IPA_IT_NAMESPACE=mycognito  -> ValueError: namespace 'mycognito' contains 'cognito',
                               which Cognito forbids in a hosted-UI domain prefix
```

The injected value passes **through** `make_namespace` rather than around it. Written the
obvious way — `injected or make_namespace()` — an injected value would never be
validated at all, because every assertion lives inside the generator, and a malformed one
would fail many minutes later as a domain-prefix rejection naming nothing relevant.

A related sharp edge, fixed while implementing: `make_namespace("")` must **raise**, not
generate. `None` means "generate"; an empty string is invalid. Otherwise a caller that
meant to inject would silently get a different namespace than it recorded, so callers
reading an environment variable pass `os.environ.get(...) or None`.

**Both teardown opt-ins are inline on recipe lines only** — verified by grep: lines 83,
102 and 117 of the `Makefile`, all recipe lines. No `export`, no file-level variable. An
ambient variable applies to every phase of every build, which is the "persists invisibly"
case the two-part opt-in exists to prevent, and declaring it ambiently would defeat the
mechanism *silently*, because the invocation that needs it still works.

**Nothing is wired.** `grep -rn "test-ci\|integration-tests" .gitlab-ci.yml
.github/workflows/` returns nothing.

The single-source namespace test scans the harness's own modules for a restated pattern
or forbidden-substring tuple. It is named for what it covers rather than for what it
implies — it cannot detect a copy in code it does not inspect.

---

## Where this leaves the feature

| Phase | State |
|---|---|
| 1 Preflight | **green** — both blocking unknowns retired |
| 2 Offline harness | **green** — 97 tests, ~5 s, $0, zero MEDIUM+ security findings |
| 3 Compose drive | **RED** — F1, F2, F3 above |
| 4 Deploy assertions | **built, run blocked** on Phase 3 |
| 5 CI seams | **green**, wired to nothing |

**Three follow-up changes, none of which belong in this feature** (Section 4 of the plan:
no skill or template defect is fixed here, because `.claude/skills/**` is public
interface and each fix needs its own bumping commit type). **Items 1 and 2 were done in
Phase 7 below**, after F3 recurred on the deploy scenario; item 3 is still open:

1. ~~**`fix(ipa):` `/ipa-compose` must resume after delegating to `/ipa-security`.**~~
   F3 — zero of eight artifacts. `ipa-compose/SKILL.md:130` says *"On success … Proceed
   to Step 2"* but nothing returns control and `/ipa-security`'s completion report reads
   as terminal. **Done in Phase 7 (F8)** — every delegation boundary now states that the
   turn must not end, and the drive nudges when the lifecycle is unfinished.
2. ~~**Harness change: decide what the answer channel actually is.**~~ F1 —
   `AskUserQuestion` is never invoked when the system prompt pre-supplies the values, so
   the resolver never fires and answers 6–9 never apply. Either stop pre-supplying so the
   questions get asked, or accept the prompt as the channel and drop the channel
   assertion. **Both options rested on a wrong diagnosis — see F9.** The call *was*
   invoked and was **rejected** by input validation, because the skill asked five
   questions in one call with a one-option namespace question. Dropping the channel
   assertion would have deleted the one check that notices. Fixed in the skill in
   Phase 7; the assertion stays and is now in both scenarios.
3. **Consider whether `/ipa-security`'s recommended default should be Route C.** F2 — an
   unattended agent picking the recommendation deploys a permissions boundary and a
   47-service policy where two roles would satisfy every gate. Not a defect; a question
   about the default. **Still open**, and the 2026-08-18 run took Route C again — though
   for the reason in F9, not by preference.

## Phase 6 — Scenario restructure and the default credential chain (2026-08-18)

Split the flat harness into a shared `harness/` package plus one folder per scenario, and
moved every AWS call onto botocore's default credential chain. **No billable run was
performed in this phase**, and no pipeline run was started.

### D6.1 — A shared package, not per-folder copies plus a loader

The comparable LaunchBridge harness solves the same problem differently:
`tests/integration/iac_deploy/_compose_modules.py:1-31` exists only because both its
scenario folders define `workspace.py` and `answers.py`, so a bare `import workspace`
resolves by `sys.path` ordering — that is, by pytest collection order, **silently**. Its
own docstring names extracting a shared package as the better fix, declined there only
because it would refactor a folder that already passed.

IPA was being restructured anyway, so it took the better fix and never needs the
workaround. Consequences recorded because they are what a reader will otherwise
rediscover:

- Scenarios import `harness.*`. No `sys.path` insertion, no explicit-path loader.
- Shared fixtures load as a **pytest plugin** (`-p harness.fixtures`) rather than being
  copied into each scenario's `conftest.py`. Copying is fewer concepts and is what
  LaunchBridge did; it was rejected because the shared fixtures contain the preservation
  rule — the logic deciding whether to delete a temp project holding `.env` and
  `scripts/*.mk`, the only documented means of teardown. Two copies of a rule that decides
  whether to destroy the means of teardown will drift, and the drift nobody notices is the
  one that deletes more. A plugin is also the only home from which pytest collects the
  `pytest_runtest_makereport` hook.
- `--import-mode=importlib` is set in every scenario's `pytest.ini`. It prevents nothing
  today — `test_compose.py` and `test_deploy.py` have distinct names — and is set now
  because the failure it prevents is **silent shadowing** rather than an error.

### D6.2 — Credentials from the default chain; the hardcoded profile deleted

`preflight.py` previously built every session as
`boto3.Session(profile_name=PROFILE, region_name=REGION)` where `PROFILE` defaulted to one
maintainer's SSO profile — which made the suite report a false negative for every other
operator and for CI, since a CodeBuild container has no named profile at all.

- `harness/aws.py` is now the single definition. `session()` pins `region_name` and passes
  **no** `profile_name`.
- The `profile` parameter is gone from `standing.live_stacks`, `sweep.list_it_stacks`,
  `reaper.{purge_versions,empty_bucket,empty_ecr,reap}` and `cognito_auth.mint_token`,
  along with every `--profile` argv element. `sweep._resolve_profile` and
  `preflight.PROFILE` are deleted. `IPA_IT_PROFILE` is retired.
- `cli_region_args()` was kept despite wrapping two list elements, as the grep-able marker
  that an argv site was **reviewed** during the removal. An inline `["--region", REGION]`
  is indistinguishable from a site that was missed.
- The region stays pinned, and the reason is unchanged: this shell exports
  `AWS_REGION=us-west-2`, and an inherited region would probe an account that is clean
  only because nothing was ever there — a false pass indistinguishable from a real one.
  `preflight._session`'s docstring argued *against* ambient credentials on those grounds;
  it was rewritten rather than left, because a docstring contradicting its own code is
  worse than none, being believed.
- The credential probe changed subject: `probe_aws_profile_resolvable` →
  `probe_credentials_resolvable`, whose detail reports
  `session().get_credentials().method`. Reporting only *that* credentials resolved would
  hide the failure worth catching — a CI build answering from a stray long-lived
  environment key instead of its task role has resolved credentials successfully and is
  still misconfigured.
- **`AWS_PROFILE` keeps a value; the harness stops authenticating with it.** These are
  separable, and conflating them is what made the problem look unsolvable.
  `harness.aws.profile_for_env()` is the only reader and supplies just the value written
  into the driven project's `.env`. It **raises** when unset rather than falling back to
  `"default"`: that fallback is accepted by `/ipa-init`, written into `.env`, and then
  fails much later inside a generated Makefile with an error naming a missing profile
  rather than the configuration step that should have supplied one.

### D6.3 — The pointer's `profile:` line became `credentials:`

`standing.render_pointer` rendered `- profile: {profile}` into the standing-resource
pointer, and `write_report` / `report_everywhere` threaded that parameter. Once teardown
takes no profile, a `profile:` line in a human-facing teardown aid is misleading — the
value available to put there is a credential resolution method, not a profile name. The
parameter and the rendered label are both now `credentials`. Not named in the plan;
recorded here as a consequence of dropping the parameter from `live_stacks`.

### D6.4 — Two path anchors had to move with their modules

`workspace.REPO_ROOT` and `preflight.REPO_ROOT` were both
`Path(__file__).resolve().parents[2]`. Moving those modules down one level into `harness/`
makes that resolve to `internal/`, not the repository root. Both are now `parents[3]`.

Neither fails loudly. `workspace` would have copied the wrong tree into the temp project,
and `preflight` would have resolved the Cognito template to
`internal/infra/cfn/cognito/cognito.yml` — a path that does not exist — so the blocking
check would have failed on a missing file rather than on anything about the account.
`standing.HERE` was re-anchored deliberately for the same reason and is covered in the
plan; these two were not, and were found by auditing every `__file__` in the package.

### F6 (finding) — the deploy tier was uncollectable, not merely unrun

`test_deploy.py:59` requested a `deploy_run` fixture **defined nowhere in the tree**.
Measured against the pre-change tree:

```
$ uv run --directory internal/integration-tests python -m pytest \
    -m "integration or teardown" --setup-plan | grep -c "fixture 'deploy_run' not found"
8
```

The distinction carries information and is the point of recording it: **an assertion suite
that was never collectable is not one that was never run — it is one nothing could have
run.** Phase 4 of this document described the deploy tier as "built; run BLOCKED", which
was true of the *drive* and not of the *suite*.

It stayed invisible because the routine free target deselects those markers, so the only
command anyone runs regularly never touched them. That is why `--setup-plan` — which walks
the whole fixture graph without executing any fixture, for free — became an acceptance
criterion rather than a nicety. After this phase the same command reports **0** errors and
the scenario collects 27 tests.

Two things followed from writing the fixture, both decisions:

- **Session scope, not module.** At module scope the fixture drives twice, once per test
  module: double the spend, double the standing infrastructure, and the teardown would
  then remove the *second* deployment while the assertions verified the *first* —
  reporting a successful verify-then-remove while the verified deployment stays up and
  billing. That is the failure the verify-before-remove ordering exists to prevent,
  reintroduced through fixture scope instead of through invocation count.
- **`FULL_MAX_BUDGET_USD` is a second variable.** `driver.py` hardcoded
  `kwargs.setdefault("max_budget_usd", 15.0)`, so `IPA_IT_MAX_BUDGET_USD` — documented as
  the spend ceiling — could not reach the only path able to spend $15. It is now
  `IPA_IT_FULL_MAX_BUDGET_USD`, kept **separate** because the ceilings differ threefold
  and each scenario sets its own inline: one shared variable set for compose would cap a
  deploy run at $5 and stop it partway through a deployment, which is indistinguishable
  from a wedge and leaves partial infrastructure standing. `max_turns` deliberately stays
  a literal — a turn ceiling is a runaway-loop backstop, and making it configurable
  invites raising it to get past a wedge.

### F7 (finding) — `AWS_PROFILE` is contradicted across five shipped skills

This is in **public interface** and it blocks a documented customer path, not merely this
harness.

| Source | Says |
|---|---|
| `ipa-init/SKILL.md:21,126` | **Optional** — "omit to use default credential chain"; Skip omits the line from `.env` |
| `ipa-compose/VALIDATION.md:21` | **Required** — "STOP immediately… do NOT generate any artifacts" |
| `ipa-prepare/SKILL.md:91` | **Required** — "Missing `AWS_PROFILE`. Run `/ipa-init`." |
| `ipa-security/SKILL.md:73` | **Required** — "STOP" |
| `ipa-destroy/SKILL.md:74` | **Required** |
| `ipa-compose/MAKEFILE_TEMPLATES.md:787` | Generated Makefiles are built for it being **empty**: "The `$(if …)` conditional ensures CI/CD compatibility when `AWS_PROFILE` is empty" |

So IPA's *generated artifacts* already support the default credential chain while IPA's
*skills* refuse to run without a profile. **Consequence for a customer: someone following
`/ipa-init`'s documented "omit to use default credential chain" path cannot then run
`/ipa-compose` at all.**

**Not fixed here.** This phase works around it with a credential-less shim profile in
CodeBuild. The fix is four small edits making the key optional in the four validation
tables, and it belongs in its own change with a `fix:` type, because `.claude/skills/**`
is public interface.

### Two properties are INFERRED, not measured

Recorded as inferred rather than asserted, and confirmed only by the first CodeBuild run —
which no phase of this work starts:

1. A `boto3.Session` with no explicit profile resolves the **container role** while
   `AWS_PROFILE=ipa-it` is exported.
2. The AWS CLI given `--profile ipa-it` for a **credential-less** profile falls through to
   container credentials.

Both follow from botocore dropping only `env_provider` — the chain link that reads
`AWS_ACCESS_KEY_ID` from the environment — when a profile is configured, while retaining
`container_provider`, the link that reads the ECS task role. That is an inference from the
documented resolution order, not an observation from inside CodeBuild. The install phase's
credential check is positioned so that if the inference is wrong, the build fails there —
for free — rather than mid-drive after spending.

### Corrections to earlier phases of this document

- **The free suite has 99 tests.** Measured: `99 passed in 4.49s`. Earlier sections of
  this document say 100 and 97; both were approximate. Nothing was dropped in the move.
- **The five free test modules lost their `test_offline_` prefix**
  (`test_answers.py`, `test_artifacts.py`, `test_reaper.py`, `test_redaction.py`,
  `test_workspace.py`). The prefix distinguished free from billable when both sat in one
  directory; `harness/tests/` now does that. Earlier cites in this document to
  `test_offline_*.py` refer to these files.
- **Every module path in Phases 1–5 above moved into `harness/`.** A cite to
  `preflight.py:161` means `harness/preflight.py`.
- **The documented pytest invocation was wrong.** Recipes must use
  `uv run python -m pytest`, not `uv run pytest`: only `-m` places the working directory
  on `sys.path`, which is the mechanism that makes `harness` importable without a build
  backend. With the bare console script every module fails with
  `ModuleNotFoundError: No module named 'harness'`. Measured, not assumed.
- **The "Where this leaves the feature" table above predates this phase.** The deploy
  tier's "built, run blocked" now reads "collects and sets up; drive blocked on F3", and
  the flat tier names map onto the two scenario folders.
- **Phase 1's probe table still names a maintainer's profile, and that is deliberate.**
  Its `aws_profile_resolvable` row is a **verbatim** record of a run on 2026-08-17, under
  a column header that says verbatim. Rewriting it to match the current design would
  falsify a dated observation, so it stands as history. The `## Target` table at the top of
  this document *was* updated, because that one describes the current target rather than a
  past run. The probe itself no longer exists under that name — see D6.2.

---

## Phase 7 — First deploy drive (run 2026-08-18)

The deploy scenario ran for the first time. It **reproduced F3 exactly**, on the full
lifecycle rather than the compose scope, and produced two further findings — one of which
corrects F1's diagnosis.

### Measured, not predicted

| | |
|---|---|
| Namespace | `itab40e6228e` |
| Account | `369530416671`, profile `vincilb+ip-dev-Admin` — **not** the `450282238889` in this document's `## Target` table |
| Drive | `$1.5159828`, 49 turns, 363.0 s wall clock |
| Result | `ResultMessage(subtype='success', stop_reason='end_turn')`, `is_error=False` |
| Ceiling | **Not** reached — `stopped_by_ceiling=false` against a `$15` ceiling and 600 turns |
| Stacks created | **one**: `itab40e6228e-dev-security`, `CREATE_COMPLETE` |
| Artifacts generated | **none** of the eight |
| pytest | `15 failed, 1 passed, 5 deselected, 6 errors in 373.32s` |
| Transcript | 1,076 events, `transcript-itab40e6228e.jsonl` |

The single pass was `test_expected_stack_exists_and_is_healthy[security]` — the one
assertion about the one free stack a truncated run happens to create.

The account mismatch is recorded rather than corrected: the run authenticated through
`AWS_PROFILE`, and which account the harness should target is a separate decision. Every
figure above is from that account.

### F8 — the lifecycle ended at the compose→security handoff, again

F3, on the deploy scenario, with the agent's own reasoning visible this time
(transcript event 1074, verbatim):

> *"Since this is running in mode=init (called from /ipa-compose), I should return
> control to the compose process with a completion message."*

It printed the completion message and ended its turn. **Printing a report is what it
took "return control" to mean** — which is the whole defect: a skill is loaded into the
calling turn, so there is nothing to return to, and the only continuation is the agent
carrying on. `/ipa-security/SKILL.md:476` said *"return control to compose silently"*
while Step 8.4 above it specified a report block that reads as terminal, and the agent
did both.

Sequence, from the transcript: `Skill ipa-init` (70) → `Skill ipa-compose` (334) → four
stack skills read (472–532) → `Skill ipa-security mode=init path=C` (579) → stack
deployed → end of turn. `/ipa-prepare` and `/ipa-deploy` never ran, and neither
`prepare:proceed` nor `deploy:proceed` appears in `gates_seen`.

**What made it expensive to read**: nothing checked that the lifecycle finished, so the
first thing to notice was `describe_stacks` on a stack nothing had created — twenty-one
times, in `botocore` tracebacks naming neither `/ipa-compose` nor the turn that ended.
The compose scenario already had the three gates that would have named it
(`test_compose.py:51,55,76`); the deploy scenario had none.

### F9 — `/ipa-init`'s `AskUserQuestion` call was REJECTED, which corrects F1

F1 recorded that `AskUserQuestion` was never invoked and attributed it to the appended
system prompt pre-supplying the values. **That diagnosis was wrong, and the correction
matters because it changes the fix.** The call *was* invoked (event 201) and was rejected
before rendering (event 202, verbatim):

```
InputValidationError:
  questions[2].options — Too small: expected array to have >=2 items
  questions          — Too big: expected array to have <=4 items
```

`AskUserQuestion` accepts at most **4** questions per call and requires at least **2**
options per question; the built-in "Other" path does not count toward the minimum.
`/ipa-init/SKILL.md:111` mandated a single call with **five** questions, and its
`APP_NAMESPACE` question offered exactly one option, `"app" (Recommended)` — so the call
broke both limits at once and **could never have succeeded on any run, attended or not**.
The agent then wrote `.env` itself from the pinned values in the appended prompt, which
is why F1 read as "the prompt was the only channel".

Consequences, which are wider than F1 concluded:

- The whole of `harness/answers.py` has never applied to any run. Answers 6–9 are
  untested not because the agent preferred its own defaults but because no batch ever
  reached the hook.
- F2 (Route C instead of Route A) follows from this rather than from agent preference.
  The 2026-08-18 run took Route C again.
- The recommended fix in F1 — *"accept that the prompt is the channel and drop the channel
  assertion"* — would have deleted the one assertion that notices, and left every real
  `/ipa-init` user eating a rejected tool call. **Do not do that.**

### F10 — the delegation letters are crossed (found by inspection, not measured)

`/ipa-compose` Step 1.5 offers A) Existing Role ARN, B) Managed Policy ARN,
C) Innovation Builder Stack, and passed `path={A|B|C}` to `/ipa-security`, whose steps
are 3a Managed, 3b Existing, 3c Innovation. **Two of the three letters mean different
things on each side.** `path=A` invites Step 3a and prompts for a managed policy where
the builder asked to supply their own role ARNs; only `C` happens to line up, which is
the path both measured runs took, which is why no run has hit this.

Recorded as inspection, not observation: no run has exercised `path=A` or `path=B`.

### The gate scanner's false positive recurred

`compose:overwrite` was recorded again, and again the matching text was
`/ipa-compose`'s own SKILL.md prose echoed into assistant output when the skill loaded —
not a question. As in Phase 3: the record is verbatim, so the false positive is visible
on inspection, but a gate count is still not a gate-crossing count.

### D7.1 — the completion gate fails the FIXTURE, not each assertion

`harness/lifecycle.py` now decides what "finished" means — all eight artifacts present,
all seven stacks live — and `deploy/conftest.py` asserts it in `deploy_run`. The predicate
lives in the shared package rather than the scenario because a scenario conftest is
unreachable from the offline suite, and this is the function that decides whether a
billable run gets re-queried. One inaccurate `subtype='success'`
therefore produces one message naming what is missing, instead of twenty-one failures
naming stacks nothing created.

Failing in the fixture is safe **because `test_teardown.py` depends on `namespace` and
`temp_project`, never on `deploy_run`** — so the teardown path and the standing-resource
report both still run. That was checked before choosing fixture-level over a first test.

The predicate reads disk and AWS, never the agent's account of what it did, and
`harness/standing.py` now holds `EXPECTED_TIERS` as the single definition so the gate and
the seven-stack assertions cannot disagree.

### D7.2 — the drive nudges, bounded at two, and counts every nudge

`driver.drive` takes an `is_complete` predicate and re-queries the same client when the
turn ends with the lifecycle unfinished. A ceiling stop is never nudged.

**The nudge is a backstop, not the fix** — the fix is in the skills. Every nudge is
counted on `RunResult.nudges`, recorded in the transcript, and printed, so a run that only
completed because it was pushed reports that instead of looking clean. `IPA_IT_MAX_NUDGES=0`
measures the skills as authored. The cap is 2 deliberately: raising it converts "a skill
stops early" into "the harness pays repeatedly to push it through", hiding the defect the
counter exists to report.

### D7.3 — the standing-resource report stopped calling one IAM stack BILLABLE

The 2026-08-18 warning read *"1 BILLABLE stack(s) left standing"* about a stack holding
four IAM roles, a permissions boundary and a policy — nothing charged for. The report now
classifies by tier (`security` free; everything else, including anything unrecognised,
billable) and says how many of the standing stacks are billable. A report that overstates
teaches a maintainer to discount it, which is the wrong lesson on the day the standing
stack is a CloudFront distribution and two Lambdas.

### What was changed, and what remains unmeasured

Fixed in this change: `/ipa-init` asks 4+1 with two namespace options (F9);
`/ipa-security` and `/ipa-compose` state the continuation obligation at every delegation
boundary, and `/ipa-init` does too for compose's auto-init gate (F8); `path=` is passed by
name with the letter mapping documented (F10); plus D7.1–D7.3 and fifteen offline
tests (`harness/tests/test_nudge.py`), taking the free suite from 99 to 114.

**Neither scenario has been re-run.** The skills' behaviour under the new instructions is
unobserved, this scenario's cost is still unmeasured, and the twenty deployment assertions
are still unexercised. `nudges=` on the next run is the measurement that matters: zero
means the skills now carry themselves through, and anything above zero means one still
stops early and the harness pushed it.

## Phase 8 — The fixes hold; one test was wrong (run 2026-08-19)

Phase 7 closed by naming `nudges=` as the measurement that mattered. **It came back zero.**
The skills carried the lifecycle from `/ipa-init` to seven deployed stacks without the
harness pushing them once, and `AskUserQuestion` fired for the first time in the project's
history — five calls, every one answered by the resolver.

### Measured, not predicted

| | |
|---|---|
| Namespace | `it9047b2a99f` |
| Source | commit `e63b197`, clean tree, 715 files |
| Driver model | `us.anthropic.claude-sonnet-4-20250514-v1:0` |
| Drive | `$4.3093221`, 98 turns, 1919.9 s (32.0 min) wall clock |
| **Nudges** | **0** — `incomplete_reason=""`, so the completion gate passed on its first check |
| Ceiling | **Not** reached — `stopped_by_ceiling=false` against `$15` and 600 turns |
| Stacks created | **all seven**, 6 of them billable |
| Artifacts generated | **all eight** (the gate would not have passed otherwise) |
| `ask_user_question` | **5** events, all `via=pre_tool_use_hook`, all with `answers` populated |
| Gates | 5: `compose:overwrite`, `security:deploy`, `prepare:proceed`, `deploy:proceed`, `deploy:build_failed` |
| pytest | `1 failed, 22 passed, 5 deselected, 1 warning in 1946.63s` |
| Transcript | 3,381 events, `transcript-it9047b2a99f.jsonl` |

Cost is now measured rather than bounded: **`$4.31`**, against the `$15` ceiling that was
chosen without data. The drive is 2.8× Phase 7's spend for 2.0× the turns — Phase 7 stopped
at a tenth of the lifecycle, so its `$1.52` was never a useful estimate of anything.

### What this settles about F8, F9 and F10

All three were fixed by instruction changes alone, and each now has a measurement:

*   **F8** (the turn ended at the compose→security handoff, twice) — `nudges=0` with all
    eight artifacts and all seven stacks. The handoff was crossed unaided. This is the one
    that could only ever be proven by a live run, because the failure was the agent's
    reading of a sentence.
*   **F9** (`/ipa-init`'s `AskUserQuestion` call was rejected) — five accepted calls,
    split 4-then-1 exactly as re-authored. The second call carries the single IaC question.
    Every prior run in this document recorded **zero** such events; `harness/answers.py`
    had never applied to anything until this run.
*   **F10** (crossed path letters) — the security question was answered
    `Managed Policy ARN`, then `ReadOnlyAccess`, and the stack deployed. The path the
    resolver named is the path that ran.

`deploy:build_failed` and `deploy:proceed` are stamped in the **same second** (15:51:35)
from the same skill document, which is the gate-scanner false positive already recorded in
Phase 6: the scanner matches its markers against the loaded `SKILL.md` prose, not against
output. Seven healthy stacks and 22 passing assertions confirm no build failed. The scanner
is still worth narrowing, and it is still not lying about anything load-bearing.

### F11 — the queue round-trip test posted a body the API never accepted

The single failure, and it is **in the test, not in IPA**:

```
POST /api/v1/jobs -> 422: {"detail":[{"type":"missing","loc":["body","input_data"],
"msg":"Field required","input":{"prompt":"integration test job"}}]}
```

`test_a_submitted_job_leaves_pending` posted `{"prompt": "integration test job"}`. The
shipped contract is `JobCreate` — `job_type` (defaulted) and `input_data` (**required**) —
and no part of `app-lib` has ever read a `prompt` field: the worker reads
`input_data["ticket"]` (`sqs_handler.py:60`). FastAPI rejected the body at validation, so
`submit_job` never ran. The same `{job_type, input_data:{ticket}}` shape is stated
independently in three places — `job_dto.py:10`, `web-client/src/mocks/handlers.ts:84`, and
`specs/011-passenger-jobs/contracts/jobs-api.md` — and the test agreed with none of them.

The body was written from the *idea* of a job rather than from the DTO, and nothing caught
it because this assertion had never once executed: Phase 7 died before any stack existed,
and every earlier phase deselected the marker. **A test that has never run is not a test**,
and its first execution is where its own defects surface, not the subject's.

Fixed by posting the real contract with `ticket` `113803` (the spec's own example), and the
assertion message now names `job_dto.py` so the next 422 is read as a contract drift rather
than an outage. The docstring also now states the expected terminal status on a fresh
namespace: `FAILED` with `Passenger not found: 113803`, because the passenger table is
empty until someone loads it. That is not a regression — `process_job` catches every
exception, records it on the job and returns 200, so the message never reaches the DLQ and
the DLQ assertion stays green while this one still proves the worker consumed the queue.

### What remains unmeasured

The 422 means **the queue round trip itself is still unproven end to end**: the job was
never created, so nothing was enqueued, and `test_a_submitted_job_leaves_pending` has yet
to observe a single status transition. Everything either side of it — the DLQ being empty,
the event source mapping being enabled, the five queue outputs resolving — passed, so the
infrastructure is verified and the *traversal* is not. The next deploy run is the first
that will exercise it, and it is the only assertion in this file whose subject has never
executed once.
