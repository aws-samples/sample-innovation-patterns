# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two things share one tree, and confusing them causes most mistakes:

1. **IPA — the framework.** Claude Code skills (`.claude/skills/ipa-*`) plus IaC templates
   (`infra/cfn/**`, `infra/tf/**`) that compose and deploy AWS infrastructure. The skills are
   Markdown instruction documents, not executable code — Claude Code is the runtime.
2. **The reference application** the framework deploys — `app-lib/` (Python/FastAPI on Lambda) and
   `web-client/` (React/TS SPA on S3+CloudFront), plus a Helm chart in `infra/k8s/` for running
   `app-lib` in a local or real cluster.

Nothing IPA generates depends on IPA at runtime. Generated output is plain CloudFormation or
Terraform, plain GNU Makefiles, and a commented `.env` — an engineer must be able to read any
generated file and use it with the skills deleted.

## Commands

```bash
# Lint & format — run before commit. Auto-fixes app-lib (ruff), web-client (prettier+eslint),
# infra (terraform fmt). `lint-check` is the read-only CI variant.
make lint
make lint-check
make -f infra/scripts/lint.mk lint-app-lib      # or lint-web-client | lint-infra (+ lint-check-*)

# Local dev servers (separate terminals)
make dev-backend        # uvicorn on :8000
make dev-frontend       # vite dev server, proxies /api to :8000

# Local Kubernetes inner-dev loop (k3d + Helm + Tilt); pod reads a REAL deployed DynamoDB table
make doctor             # verify docker/kubectl/helm/k3d/tilt/ctlptl/aws; installs nothing
make local-setup && make local-up
make local-destroy      # or local-reset
```

```bash
# app-lib (Python 3.12, uv)
cd app-lib
make sync                                        # uv sync
make test                                        # pytest (71 tests)
uv run pytest tests/features/passengers/test_passenger_data_service.py -v   # one file
uv run pytest -k test_delete_not_found -v                                   # one test
make -C tests test-coverage
make lint-imports                                # feature import-boundary check
make lint-pynamodb                               # PynamoDB null=True check

# web-client (Vitest + jsdom + MSW)
cd web-client
npm test | npm run test:watch | npm run test:coverage
npx vitest run src/pages/JobsPage.test.tsx        # one file
npm run build                                     # tsc -b && vite build
npm run codegen                                   # regenerates services/api/generated.ts; needs backend on :8000

# docs (Docusaurus, pnpm, port 3001)
cd docs && pnpm install --frozen-lockfile && pnpm start
```

```bash
# Maintainer-only integration harness (drives the real lifecycle via the Agent SDK)
make -C internal/integration-tests               # help; creates nothing
make -C internal/integration-tests test-offline  # $0, ~5s, no AWS creds
make -C internal/integration-tests test-compose  # ~$0.94 / 6min, live AWS
make -C internal/integration-tests test-deploy   # ~$4.31 / 32min, leaves 7 stacks standing
```

## The IPA lifecycle

`/ipa-init` → `/ipa-compose` → `/ipa-prepare` → `/ipa-deploy` (plus `/ipa-destroy`, and
`/ipa-help`, which inspects project state and names the next skill). Every skill is idempotent.
`/ipa-init` writes `.env`; `/ipa-compose` writes `scripts/*.mk`; the rest only execute Makefiles.

## The stack-skill contract — the core abstraction

`.claude/skills/ipa-stack-<name>/SKILL.md` is a **machine-readable spec of one stack**, expressed as
Markdown tables that `/ipa-compose` parses:

| Section | Consumed for |
|---|---|
| Stack Identity | stack name, template path, capabilities, lifecycle, tier |
| Parameters / Feature Flags | `--parameter-overrides`, validation |
| Wirable Parameters | which other stack's output feeds which parameter |
| Outputs | `$(eval)` lookups in generated Makefiles |
| Build Requirements | `build.mk` targets (container image, SPA build) |
| Compose Config | values prompted from the builder at compose time |
| Terraform Module | the `infra/tf/` equivalent: variables, outputs, remote state |

`/ipa-compose` scans `.claude/skills/ipa-stack-*`, reads those tables, transitively auto-includes
every stack named as a wiring source, topologically sorts the result, and emits the Makefiles. Two
consequences:

- **Adding a stack is authoring, not coding.** Write the template + Terraform module + a SKILL.md
  with those tables; there is no composition code to change. Use `/ipa-author-stack`.
- **The tables are the contract.** A table that drifts from its template produces a Makefile that
  deploys with wrong parameters, and nothing in the templates will catch it. Update both together.

**Two lifecycles.** *Prepare* stacks are one-time prerequisites — `cognito`, `ecr`, `logs`,
`codecommit`, `codepipeline`, `tfstate`. *Deploy* stacks are the solution tiers — `frontend`,
`backend`, `queue`. All prepare stacks deploy before all deploy stacks.

**Tier consolidation.** There are three tier templates, not one per service. Optional resources are
feature-flagged parameters on the tier (e.g. `EnablePassengersTable` on backend, `EnableJobsTable`
on queue, `EnableSqsIntegration` which compose sets automatically when `queue` and `backend` are
composed together).

**Dual IaC.** `APP_IAC=cloudformation|terraform` is chosen at init. `infra/cfn/<tier>/` and
`infra/tf/<tier>/` must stay in parity, and each stack skill documents both. Exceptions:
`security` and `tfstate` are CloudFormation-only — `tfstate` bootstraps the Terraform backend, so
it cannot itself be Terraform.

**Not committed** (regenerated per project): `.env`, `scripts/*.mk`,
`scripts/SECURITY-DISPOSITION.md`, `infra/cfn/generated/`.

## Where the local conventions live

Read the directory's own `CLAUDE.md` before editing in it — each carries rules that are not
inferable from the code:

| Path | Covers |
|---|---|
| `app-lib/CLAUDE.md` | layout, env vars, `PynamodbUtil.env_table_name()`, ruff config |
| `app-lib/src/app_lib/features/CLAUDE.md` | Orchestration-Only Composition — features import `common/`, never each other |
| `app-lib/src/app_lib/common/CLAUDE.md`, `.../features/passengers/CLAUDE.md`, `app-lib/tests/CLAUDE.md` | shared infra, the reference feature, test conventions |
| `web-client/CLAUDE.md` | placement rules, feature flags, mock-UX mode, Vitest/MSW setup |
| `web-client/src/*/AGENTS.md` | per-module do/don't (auth, components, mocks, api) |
| `docs/CLAUDE.md` | Docusaurus conventions; read `developer-docs/docs/documentation-structure.md` before authoring pages |
| `infra/cfn/<tier>/CLAUDE.md`, `infra/k8s/CLAUDE.md`, `infra/containers/rest-k8s/CLAUDE.md` | per-template and chart conventions |
| `internal/README.md`, `internal/integration-tests/README.md` | maintainer-only tooling and costs |

## Public interface vs internal — this decides `!` on commits

**Public** (a change that breaks it is breaking): skill names/arguments and the files they generate
(`.claude/skills/ipa-*`); CloudFormation parameter names, outputs and logical IDs (`infra/cfn/**`)
and their Terraform equivalents; generated artifacts and the `.env` keys they read
(`scripts/*.mk` target names, `INSTALL-RUNBOOK.md`, `SECURITY-DISPOSITION.md`); `app-lib`'s HTTP
routes and request/response shapes; `web-client`'s `window.__CONFIG__` contract and auth flow; and
**`internal/release/templates/`**, which is public interface despite its path — it is copied into
customer projects.

**Internal** (never `!`, however large the diff): `.gitlab-ci.yml`, `.github/workflows/**`,
`infra/scripts/**`, all of `internal/**` except `templates/`,
`docs/docs/developer-docs/internal/**`, `CLAUDE.md`, `openspec/`, `specs/`, `.context/`, `.ash/`,
and the release procedure itself.

Test: *would a consumer who never maintains this repo have to do work?* If no, no `!`.

`internal/`, `.gitlab-ci.yml`, `.gitlab`, `.specify`, `docs/docs/developer-docs/internal`,
`docs/docs/guides/releasing.md` and `scripts/.gitignore` are filtered out of the public GitHub
mirror by `internal/release/publish-github.sh` — they exist on `code.aws.dev` only.

## Commits, versions, releases

The commit subject **is** the version bump and the release-notes entry; there is no VERSION file and
no committed changelog. Use Conventional Commits: `<type>(<scope>): <description>`, imperative,
lowercase, ≤72 chars. Scopes: `ipa`, `app-lib`, `web-client`, `docs`, `infra` (omit for multi-scope).

| Subject type | Bump | Release-notes section |
|---|---|---|
| `feat` | minor | Added |
| `fix` `docs` `refactor` `perf` `ci` `build` `revert` | patch | Fixed / Documentation / Changed / Performance / CI-Build / Reverted |
| `style` `test` `chore` | **none** | (skipped) |
| unmatched subject (`wip`, `Add pagination`, `Merge branch …`) | **patch** | **none** — moves the version recording nothing |
| any bumping type with `!` or a `BREAKING CHANGE:` footer | minor pre-1.0, major from 1.0 | — |

- **Never put `!` on `chore`/`style`/`test`.** They are `skip = true` in `cliff.toml`, so the `!` is
  swallowed and the breaking change becomes invisible.
- **Squash-merge every MR, and treat the MR title as release metadata.** GitLab makes the title the
  squash subject, so it must carry the *largest* bump the branch earns — a `feat` merged under a
  `fix:` title is invisible in the notes.
- **Releasing writes nothing to the repo.** Two manual GitLab jobs (`gitlab:release:preview`, then
  `gitlab:release`) tag `origin` and create a Release; `github:release` is a separate manual stage
  that publishes a chosen tag to the public mirror. Read past releases with
  `git tag -l --format='%(contents)' v0.2.1`.

## Security scanning

ASH config is `.ash/ash.yaml`. Every suppression needs `rule_id`, `path`, and a `reason` explaining
why it is safe. Note that ASH suppressions do **not** suppress GitLab Dependency Scanning
(Gemnasium) findings, and grype's coverage is not a superset of Gemnasium's — a clean grype run is
not proof a lockfile is clean.

## Known rough edges

- `make dev` is documented in the root Makefile header but has **no recipe** — use `make dev-backend`
  and `make dev-frontend`.
- `web-client/CLAUDE.md` points at `make -f scripts/test.mk test-web`; `scripts/test.mk` is a
  generated stub that reports "No tests configured". Run web tests with `npm test`.
- `specs/` and `openspec/` hold historical planning artifacts, not current state. Prefer the skills,
  templates and `docs/` for what the system does today.
