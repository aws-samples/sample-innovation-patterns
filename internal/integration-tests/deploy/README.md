# deploy scenario

Drives the full lifecycle — `/ipa-init`, `/ipa-compose`, `/ipa-prepare`, `/ipa-deploy` —
then asserts against the **live** deployment.

```bash
make test            # deploy; LEAVES THE STACKS STANDING
make test-teardown   # verify-then-remove this run's stacks
make test-ci         # deploy THEN tear down, in one run
```

## Cost: $4.31 / 32 minutes — measured

Measured once, on 2026-08-19: **`$4.3093221`, 98 turns, 1919.9 s**, completing the whole
lifecycle with zero nudges (`DECISIONS.md` Phase 8). Plus AWS charges for seven stacks for
as long as they stand.

**Budget the `$15` ceiling, not the `$4.31`.** One run on one account in one region is a
data point, not a distribution — a slower path through the same skills spends more, and the
ceiling is what this scenario is permitted to spend before it is stopped.

The ceiling is `IPA_IT_FULL_MAX_BUDGET_USD`, default 15, set **inline** on this
scenario's recipe lines.

It is **separate** from `IPA_IT_MAX_BUDGET_USD` (default 5, the compose scenario's) and
must stay separate. The two differ threefold: one shared variable set for compose would
cap a deploy run at $5 and stop it partway through a deployment — indistinguishable from
a wedge, and leaving partial infrastructure standing.

## The seven stacks

Deployed under the run's generated namespace, in this order:

| Stack | Holds |
|---|---|
| `{ns}-dev-logs` | centralised S3 log bucket |
| `{ns}-dev-ecr` | container image repository |
| `{ns}-dev-cognito` | user pool, OAuth hosted UI |
| `{ns}-dev-security` | two named IAM roles |
| `{ns}-dev-queue` | SQS + DLQ + worker Lambda + DynamoDB |
| `{ns}-dev-backend` | Lambda + API Gateway v2 + DynamoDB |
| `{ns}-dev-frontend` | S3 + CloudFront + OAC |

### They are LEFT STANDING by default

`make test` does not remove them, and that is deliberate rather than an oversight: a
standing deployment is what lets a maintainer open the application in a browser and
confirm by eye what the assertions claim.

Remove them either way:

```bash
make test-teardown                            # verify-then-remove, from here
make -C .. teardown-namespace NAMESPACE=<ns>   # by namespace, from the harness root
```

The namespace is printed by the run and recorded in `standing-resources-<ns>.md` at the
harness root, which is readable with no credentials configured.

## Status: F3's cause is fixed; this scenario has not been re-run

Both of this scenario's runs stopped at composition (`DECISIONS.md` F3 and F8): the agent
delegated to `/ipa-security`, deployed the security stack, and ended its turn with none of
`/ipa-compose`'s eight artifacts generated. The skills now state the continuation
obligation explicitly at every delegation boundary, and the drive nudges a bounded number
of times when the lifecycle is unfinished.

**The re-run on 2026-08-19 measured `nudges=0`** — all eight artifacts, all seven stacks,
the lifecycle carried by the skills themselves. `nudges=` in the drive's printed line stays
the number to read first: **zero is the only good value**, and anything above it is a skill
that still ends its turn early and was pushed through by the harness.

One assertion failed, in the test rather than in IPA: the queue round trip posted a body
`JobCreate` never accepted and drew a 422 (F11, fixed). So **the queue traversal is still
unproven** — the job was never created, nothing was enqueued, and no status transition has
ever been observed. Every other queue assertion passed, so the infrastructure is verified
and the trip through it is not.

## What it asserts

Three assertions carry **stated limits**, and each limit is in the test's own docstring so
a later reader cannot over-read it:

- The 401 check **cannot** establish that the container runs.
- The container probe is what establishes that, and needs three conditions.
- The job check stops at "left `PENDING`" — **a `FAILED` job passes it.**

Beyond those: every expected stack exists in a healthy completed state; endpoint
locations come from CloudFormation **outputs** rather than from `.env` (so one missing
`update-env-*` target fails the check that owns it instead of blanking every downstream
probe); the app is served with its runtime config; an anonymous API call is refused with
exactly 401; a real Cognito token is accepted; the DLQ is empty; and no generated
credential reaches a durable sink.

The teardown assertions add: the deployment is **verified live before anything is
removed** — ordering, not coverage, because otherwise a run that provisioned nothing and
a run that provisioned everything both end with a passing teardown; nothing remains under
this namespace; **no other run was removed**, checked against a listing that includes a
sentinel foreign namespace, because "nothing remains under this namespace" is also
satisfied by deleting the entire account; and the standing-resource pointer is removed
only for a confirmed deletion.

## Files

Six — the five a scenario needs, plus a second test module:

| File | Holds |
|---|---|
| `Makefile` | `help` (default), `test`, `test-teardown`, `test-ci`, `clean` |
| `pytest.ini` | this scenario's `integration` and `teardown` markers, plus the plugin |
| `conftest.py` | `deploy_run` — session-scoped, and the only thing here that spends |
| `README.md` | this file |
| `test_deploy.py` | the live-deployment assertions |
| `test_teardown.py` | verify-then-remove, behind the two-part opt-in |

Everything else — `credentials`, `resolver`, `namespace`, `transcript`, `temp_project` —
comes from `harness.fixtures`, loaded as a plugin by `pytest.ini`'s `-p` flag.

`deploy_run` is **session**-scoped. At module scope it would drive twice, doubling spend
and standing infrastructure, and the teardown would then remove a different deployment
than the assertions verified — passing while the verified deployment stays up and billing.
