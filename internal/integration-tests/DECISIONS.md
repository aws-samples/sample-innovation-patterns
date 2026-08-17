# IPA Integration Tests — Decisions and Measurements

Findings that would otherwise live only in a git-ignored temp project, and be lost
with it. Every figure here is **measured**, never predicted.

---

## Target

| | |
|---|---|
| **Account** | `450282238889` |
| **Caller** | `arn:aws:sts::450282238889:assumed-role/Admin/vincilb-Isengard` |
| **Profile** | `peterpyu+code-evaluation-Admin` |
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
interface and each fix needs its own bumping commit type):

1. **`fix(ipa):` `/ipa-compose` must resume after delegating to `/ipa-security`.**
   F3 — zero of eight artifacts. `ipa-compose/SKILL.md:130` says *"On success … Proceed
   to Step 2"* but nothing returns control and `/ipa-security`'s completion report reads
   as terminal.
2. **Harness change: decide what the answer channel actually is.** F1 — `AskUserQuestion`
   is never invoked when the system prompt pre-supplies the values, so the resolver never
   fires and answers 6–9 never apply. Either stop pre-supplying so the questions get
   asked, or accept the prompt as the channel and drop the channel assertion. This is a
   Phase 3 re-run, not a skill change.
3. **Consider whether `/ipa-security`'s recommended default should be Route C.** F2 — an
   unattended agent picking the recommendation deploys a permissions boundary and a
   47-service policy where two roles would satisfy every gate. Not a defect; a question
   about the default.
