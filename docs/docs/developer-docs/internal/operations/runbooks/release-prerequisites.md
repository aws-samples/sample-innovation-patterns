---
title: Release Prerequisites
sidebar_position: 11
---

# Release Prerequisites

This runbook answers four questions about the GitLab project that decide how the
MR-gated release flow can be built:

1. Can a job token push a branch to this repository?
2. Is `release/*` unprotected, and is `v*` protected?
3. Do MR-creating push options work with a job token?
4. What CI runs on a branch that is not `main`?

Each question is **observed, not assumed**. Three places in this repository assert
that `CI_JOB_TOKEN` cannot push a branch. GitLab documents the opposite: branch
push with a job token was introduced in 17.2 behind the feature flag
`allow_push_repository_for_job_token`, enabled on GitLab.com in 18.3, and became
generally available in 18.4 with the flag removed. The narrower claim that remains
true is that a job token cannot push to a **protected** branch, and `main` is
protected. The generalisation is what went out of date.

:::warning Results are facts about an instance at a point in time
Every row in the results table records a date and an observer. These are
observations of `code.aws.dev` as it was configured on that date, and a GitLab
upgrade or a settings change invalidates them. Re-run the checks rather than
trusting a stale row.
:::

Checks 1 and 2 require **Maintainer or Owner** on the project. Checks 3 and 4
require running a pipeline.

## Results

| # | Fact | Observed | Date | Observer |
|---|------|----------|------|----------|
| 1a | *Allow Git push requests to this project's repository* setting is present | `unverified` | — | — |
| 1b | That setting is enabled | `unverified` | — | — |
| 2a | No protected-branch rule matches `release/*` | `unverified` | — | — |
| 2b | `v*` appears under Protected tags | `unverified` | — | — |
| 3a | A job-token push creates a branch on origin | `unverified` | — | — |
| 3b | `-o merge_request.create` creates an MR with a job token | `unverified` | — | — |
| 3c | A pipeline ran on the job-token-pushed branch (expected: **no**) | `unverified` | — | — |
| 4 | Jobs that appear on a non-default branch pipeline | `unverified` | — | — |

Row 3c expects **no**. GitLab states twice that a job-token push triggers no
pipelines. Observing that confirms the release flow's trigger design: nothing CI
pushes can start a pipeline, so the automatic release job must trigger on the
pipeline created by a human's merge.

## Check 1: The job-token push setting

To read the setting, open **Settings > CI/CD > Job token permissions**.

Record two things:

- **Whether the setting exists.** *Allow Git push requests to this project's
  repository* requires GitLab 17.2 or later. Its absence means the instance
  predates 17.2, check 3 cannot succeed, and the fallback in
  [Consequences](#consequences) applies. Stop here in that case — the remaining
  checks cannot change the outcome.
- **Whether it is enabled.** It is **off by default** and requires Maintainer or
  Owner to change. The equivalent API parameter is
  `ci_push_repository_for_job_token_allowed`.

Enable it only with the agreement of a project Maintainer or Owner. See
[Security note](#security-note-on-enabling-job-token-push) before doing so.

The instance version cannot be read from `/api/v4/version` — that endpoint is
Midway-gated and returns a redirect to token-authenticated callers. The presence
or absence of the setting in the UI answers the same question directly.

## Check 2: Branch and tag protection

To read branch protection, open **Settings > Repository > Protected branches**.
Confirm that no rule matches `release/*`. A wildcard rule such as `*` or `rel*`
would match, so read the patterns rather than looking for the literal string.

To read tag protection, open **Settings > Repository > Protected tags** and record
whether `v*` appears.

:::note Tag push is already known to work
CI created and pushed `v0.1.7` and `v0.2.0`. `git cat-file tag v0.2.0` shows
`tagger GitLab CI <ci@code.aws.dev>`, which is artifact evidence rather than
inference. Row 2b is recorded for completeness; it does not gate anything.
:::

## Check 3: The throwaway probe

This check pushes one throwaway branch from a CI job and observes three separate
outcomes. It is the decisive check: whether push options are honoured for a
job-token push is not stated in GitLab's documentation.

:::warning Do not commit this job
The snippet below exists for one pipeline run. Add it to `.gitlab-ci.yml` in your
working tree, push it to a scratch branch or run it from a pipeline on `main`
without committing it to history, and revert the edit afterwards. Committing and
reverting a probe puts two commits in the release history and leaves a window in
which someone can run it by accident.
:::

Add this job temporarily:

```yaml
probe:job-token-push:
  stage: release
  image: public.ecr.aws/docker/library/python:3.12-bookworm
  variables:
    GIT_DEPTH: "0"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_COMMIT_TAG == null
      when: manual
      allow_failure: true
    - when: never
  needs: []
  script:
    - git config user.email "ci@code.aws.dev"
    - git config user.name "GitLab CI"
    - BRANCH="probe/job-token-$CI_JOB_ID"
    - git checkout -b "$BRANCH"
    - git commit --allow-empty -m "chore: job-token push probe"
    - git remote set-url origin "https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
    - |
      git push \
        -o merge_request.create \
        -o merge_request.target="$CI_DEFAULT_BRANCH" \
        -o merge_request.title="DO NOT MERGE — job-token probe $CI_JOB_ID" \
        -o merge_request.description="Throwaway probe for the release prerequisites runbook.\nDelete this MR and its branch." \
        origin "$BRANCH"
    - echo "pushed $BRANCH — now check origin for the branch, the MR, and any pipeline"
```

Two constraints are already applied above and matter if you adapt the snippet:

- **Literal newlines in push option values are rejected** with
  `fatal: push options must not have new line characters`. Use `\n`, which GitLab
  converts to real newlines in the description.
- **A target is required** when pushing from the default branch, so
  `-o merge_request.target` is passed explicitly.

`-o ci.skip` is available but unnecessary — a job-token push starts no pipeline.

Run the job, then record three outcomes separately:

- **3a — did the branch appear on origin?** Check **Repository > Branches**.
- **3b — did an MR appear?** Check **Merge requests**. This can fail while 3a
  succeeds, and that partial outcome selects a different fallback than a total
  failure does. Record them independently.
- **3c — did a pipeline run on that branch?** Check **Build > Pipelines** filtered
  to the probe branch. Expect none.

## Check 4: What runs on a non-default branch

Fold this into check 3's single pipeline run — if a pipeline appeared for the probe
branch, record which jobs it contains. If none appeared (the expected result for
3c), the answer comes from reading the `rules:` in `.gitlab-ci.yml` instead, and
should be recorded as derived rather than observed.

What is known from the configuration:

- All release and publish jobs gate on
  `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_COMMIT_TAG == null` and
  terminate in `- when: never`, so none of them runs on a non-default branch.
- `pages` gates on the default branch alone, so it does not either.
- Of the two included components, only **`ash`** gates anything: `release` and
  `release:auto` declare `needs: [job: ash, optional: true]`. Whether `ash`
  itself runs on a non-default branch is what this check establishes.
- **`acq` gates nothing.** No job declares a `needs:` on anything it provides, and
  `.gitignore` ignores `.acq/`, so its output is local scratch. It cannot block a
  release branch.

This check determines only how long a release MR takes to become mergeable, not
whether the flow works.

## Consequences

Read the recorded results against this table and state the outcome in
[Decision in force](#decision-in-force).

| Observation | Consequence |
|---|---|
| 1a is **no** (setting absent, instance predates 17.2) | A job token cannot push a branch here. The release-preparation job needs a project access token with `api` scope, stored as a masked CI variable, and the project accepts a rotating credential it has so far avoided. |
| 1a **yes**, 1b **no** | The capability exists but is off. A Maintainer or Owner enables it, then check 3 is re-run. Nothing is blocked permanently. |
| 3a **no** (push refused) | Same fallback as 1a being no: a project access token with `api` scope. |
| 3a **yes**, 3b **no** (branch created, no MR) | CI pushes the branch and prints a link; a human opens the MR. This keeps the job token and costs one manual step per release. Preferred over introducing a rotating credential. |
| 3a **yes**, 3b **yes** | The release-preparation job is one `git push`. No new credential. |
| 3c **yes** (a pipeline ran) | Contradicts GitLab's documented behaviour and invalidates the assumption that no loop guard is needed. Add `-o ci.skip` to the push and re-examine the automatic release job's trigger. |
| 2a **no** (`release/*` is protected) | A job token cannot push to it. Either exclude `release/*` from the protection rule or fall back to a project access token. |

### Decision in force

`unverified` — no checks have been performed yet. Fill this in with the selected
path and the date once the table above is complete.

## Security note on enabling job-token push

Enabling *Allow Git push requests to this project's repository* widens what any
job token issued for this project can do. Three properties bound the exposure:

- **The token inherits the permissions of the user who started the job.** A job
  token cannot push where the person who clicked the button could not push.
- **Protected-branch rules still apply.** With `main` protected, a job token
  cannot push to `main` whatever this setting says. That is the property the
  release flow depends on — the release branch is writable and the trunk is not.
- **The token's lifetime is the job's lifetime.** It cannot be exfiltrated for
  later use in the way a project access token can.

Enabling it is a Maintainer or Owner decision, not an implementation step. Record
who enabled it and when in the results table.

## Cleanup

Complete every item. The probe is designed to leave nothing behind.

- [ ] Delete the probe branch on origin (**Repository > Branches**, or
      `git push origin --delete probe/job-token-<id>`)
- [ ] Close **and** delete the throwaway MR — a closed `DO NOT MERGE` MR still
      appears in searches
- [ ] Revert the working-tree edit: `git checkout -- .gitlab-ci.yml`
- [ ] Confirm `git ls-remote --heads origin` lists no `probe/*` branch and no
      unexpected `release/*` branch
- [ ] Confirm the probe job is not present in `.gitlab-ci.yml` on `main`
- [ ] Delete the local probe branch: `git branch -D probe/job-token-<id>`

## Related

- [Releasing](releasing.md) — the release flow these prerequisites gate
