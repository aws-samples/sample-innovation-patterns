# compose scenario

Drives `/ipa-init` then `/ipa-compose`, and **stops before `/ipa-prepare`**. The stop is
the point: a composition defect found here costs about a dollar, and the same defect
found by the `deploy` scenario costs about fifteen.

```bash
make test        # the drive
make -C ../ teardown-namespace NAMESPACE=<ns>   # remove what it left standing
```

## Status: was RED on F3; the cause is fixed and this has not been re-run

This scenario's last run failed for a cause **outside itself**: `/ipa-compose` generated
none of its eight artifacts, because nothing brought the agent back from `/ipa-security`
(`DECISIONS.md` F3). The skills now state the continuation obligation at every delegation
boundary, and the drive nudges when the artifacts are still absent.

Two things to read on the next run, in this order:

1. **`nudges=` in the printed drive line.** Zero means the skills carried themselves
   through. Above zero means one still ends its turn early and the harness pushed it —
   the run may pass, and the defect is real.
2. **`test_the_answer_channel_is_recorded`.** Until 2026-08-18 `/ipa-init` batched five
   questions with a one-option namespace question, which `AskUserQuestion` rejects
   outright, so no batch was ever answered and `harness.answers` went unused. That
   assertion is what notices.

## Cost: $0.9417 over 377.8 s — measured

**Measured, not estimated.** Recorded in `DECISIONS.md` Phase 3 from an actual run. The
figure covers model spend for the drive.

The ceiling is `IPA_IT_MAX_BUDGET_USD`, default 5, set **inline** on this scenario's
recipe lines so it cannot leak into a deploy run on the same machine. The deploy
scenario has its own, separate ceiling for the same reason.

## What it creates

One real stack: `{ns}-dev-security` — two named IAM roles.

They are **free but real**. The scenario is described as creating no billable
infrastructure, which is true and easy to over-read as creating nothing at all. Left
alone, it is one role pair per iteration.

Remove them from the harness root:

```bash
make teardown-namespace NAMESPACE=<ns>
```

The namespace is printed by the run and recorded in
`standing-resources-<ns>.md` at the harness root.

## What it asserts

Grouped by what each group would otherwise miss silently:

- **The run reached compose and stopped.** No ceiling stopped it; `scripts/deploy.mk`
  exists; nothing was deployed beyond the security stack.
- **The harness's answers reached the skills.** `APP_NAMESPACE` equalling the generated
  namespace is the *only* discriminator — every other pinned answer is also the skill's
  own recommended option, so agreement on those is consistent with no answer having been
  delivered at all.
- **All eight artifacts exist.** The claim is the skill's own and had never been observed
  on a real run.
- **The composed architecture.** Tier set, per-tier prepare targets, the cross-tier SQS
  wiring, and teardown being the exact reverse of deploy.
- **The two costly defects.** `build.mk` referencing `web-client/` rather than a
  non-existent `frontend/`, and `env.mk` declaring both `update-env-*` targets — whose
  absence is *fully* silent: the deployment succeeds and the frontend is served a config
  naming no API and no identity provider, failing in the browser with nothing in any
  deployment log.

## Files

Five, and this is the set a new scenario needs:

| File | Holds |
|---|---|
| `Makefile` | `help` (default), `test`, `test-ci`, `clean` |
| `pytest.ini` | this scenario's `integration` marker, plus the shared-fixtures plugin |
| `conftest.py` | `compose_run` — the drive, and the only thing here that spends |
| `README.md` | this file |
| `test_compose.py` | the assertions |

Everything else — `credentials`, `resolver`, `namespace`, `transcript`, `temp_project` —
comes from `harness.fixtures`, loaded as a plugin by `pytest.ini`'s `-p` flag rather than
copied.
