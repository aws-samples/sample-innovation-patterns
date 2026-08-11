# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-08-11

### Fixed
- **ipa** — Add MR-gated release flow with automatic tag on merge

  Cutting a release was a single button press that tagged origin
  immediately, with no review of the notes and no enforcement that
  CHANGELOG.md had been regenerated. That produced v0.2.0, whose committed
  changelog read "## [Unreleased]" while the tag and the published Release
  both said 0.2.0 — the changelog step was documented as optional.
  
  The release is now prepared as a merge request and tagged by merging it:
  
    release:prepare  regenerates CHANGELOG.md on release/vX.Y.Z and opens
                     an MR. Creates no tag.
    release:auto     automatic on every push to main. Tags and creates the
                     GitLab Release when a release MR was merged.
  
  Merging is the approval, so the notes are read as a diff before anything
  irreversible exists.
- **ipa** — Accept detached HEAD in release-prepare branch guard

  A GitLab runner checks out a detached HEAD ("Checking out <sha> as
  detached HEAD (ref is main)"), so `git rev-parse --abbrev-ref HEAD`
  returned the literal string "HEAD" and never "main". The precondition
  guard was written for a local run, so release:prepare rejected its own
  CI job on every invocation and had never succeeded in CI.
  
  Prefer CI_COMMIT_BRANCH, which GitLab sets to the branch the pipeline
  ran for even on a detached checkout. This does not weaken the guard: the
  job rule already gates on $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH, the
  variable is set by GitLab rather than the script, and locally it is unset
  so the rev-parse form applies unchanged.
  
  The other release paths were unaffected because none asks what branch it
  is on — release-run.sh tags HEAD, which works detached. That is why only
  this job failed.

## [0.2.0] - 2026-08-07

### Added
- Add UX-first mocking mode to web-client

  Promote the existing test-only MSW into a browser worker so the web-client
  can run entirely against mocks during `npm run dev`, with a transparent
  runtime toggle and self-teaching agent context.
  
  - Share one handler set (src/mocks/handlers.ts, relative URLs) between the
    Node test server and a new browser worker (src/mocks/browser.ts)
  - Add a top-level MOCK_API runtime config key; gate the worker on
    PROD===false && config.MOCK_API via a lazy import in main.tsx so MSW is
    tree-shaken out of production builds; default it off everywhere including
    the deploy writer (configure_frontend.py)
  - Fix SettingsPage rendering booleans (false) as the "empty" badge
  - Pin jsdom origin to http://localhost in vitest.config so relative handlers
    match in tests; add a FeatureFlags index signature so config is assignable
    to flagged's FeatureGroup (pre-existing build break from the 029 migration)
  - Generate mockServiceWorker.js via postinstall + gitignore (mirrors OIDC)
  - Encode mock-UX mode + the mock-to-real migration loop in co-located
    AGENTS.md/README.md/CLAUDE.md context across web-client and app-lib
  - Document the workflow: developer-docs reference page + builder guide
- **infra** — Two-stage manual release — derived internal releases + selective GitHub publish
- **infra** — Add turnkey k3d + Helm + Tilt local inner-dev loop

  Recorded retroactively. This work shipped across 4eed52b, 6a3b62a,
  3e5689b, 4e94812, 894dd0a, df88477, df17002 and f4cbde6, every one of
  which carries a non-conventional "Update: modify N file(s)" subject.
  Such subjects are skipped by cliff.toml, so the largest feature in the
  v0.1.7..HEAD window derived no version bump and appeared in no
  changelog section. This commit is empty; it adds no code, only the
  record that the code exists.
  
  Builders can now develop the app-lib FastAPI service against Kubernetes
  locally. `make local-setup && make local-up` stands up a k3d cluster
  plus local registry via ctlptl, builds a plain-uvicorn:8000 container
  (infra/containers/rest-k8s/, additive to the existing Lambda
  rest-lambda image), and deploys the Helm chart through Tilt with
  live-update on app-lib/src edits and a :8000 port-forward. The root
  Makefile gains doctor, local-setup, local-up, local-destroy and
  local-reset. doctor checks the six required CLIs plus the AWS CLI,
  prints exact install commands, and fails fast rather than
  auto-installing or leaving a partial cluster behind.
- **infra** — Read the real deployed DynamoDB table from the local pod

  Recorded retroactively for the same reason as the preceding commit.
  
  The split-plane model: the data plane (DynamoDB) is stood up by the
  existing /ipa-compose then /ipa-prepare then /ipa-deploy flow against
  the backend tier, and only the compute plane runs locally in k3d. The
  two converge by table-name convergence, since PynamodbUtil
  env_table_name and backend.yml both build the same
  {APP_NAMESPACE}_{APP_ENV}_passengers name, plus host-mounted ~/.aws
  credentials. The Tiltfile injects the APP_NAMESPACE, APP_ENV,
  AWS_REGION and APP_REGION convergence trio from the repo-root .env via
  dotenv() into helm(set=[...]), so the local pod resolves the same table
  the backend tier created. No CFN-output wiring and no helm compose mode
  were needed, leaving /ipa-compose untouched. Tilt verifies credentials
  with aws sts get-caller-identity before the pod starts, so it never
  comes up against dead credentials.
- **infra** — Add cloud-ready app-lib Helm chart for cluster handoff

  Recorded retroactively for the same reason as the preceding commits.
  
  The chart is the customer handoff artifact: Deployment, Service,
  ServiceAccount, helpers and NOTES, production-shaped by default (auth
  on, one replica, resource limits) and re-pointed per environment by
  values overlays. The AWS-credential mount is gated by an
  aws.credentials.mode toggle: none for cloud IRSA, direct for a host
  mount, and initCopy (the default) where an init container copies host
  credentials into an emptyDir so non-root pods can read them. The
  ServiceAccount is IRSA-annotatable and image, env and resources are
  values-overridable, so the chart targets a real cluster with helm
  alone: no IPA, no Claude Code, no chart edits. An annotated,
  deliberately non-deployed infra/k8s/envs/eks/ overlay (template only,
  placeholder account ID 123456789012) shows what a cloud overlay looks
  like.
- **ipa** — Add /ipa-k8s-help local and EKS guidance skill

  Recorded retroactively for the same reason as the preceding commits.
  
  An optional Claude Code helper that is the interactive counterpart to
  `make doctor`. Local scope runs a seven-step check-and-instruct flow
  covering tools, credentials, table-name convergence, table existence,
  cluster state, a guided run, and symptom-to-remediation triage. EKS
  scope walks the eks/ overlay and validates cloud pre-conditions,
  treating infra/k8s/envs/eks/CLAUDE.md as the single source of guidance.
  It checks and instructs only: it never auto-installs and never applies
  to a cluster. Its description disambiguates it from /ipa-help, which
  inspects IPA lifecycle state.


### Changed
- **web-client** — Replace react-feature-flags with flagged

  Swap the react-feature-flags dependency for flagged, a zero-dependency,
  TypeScript-native React feature-flag library. FlagsProvider now consumes
  config.features directly as an object map, eliminating the getFlags() array
  adapter and the hand-written type shim (flagged ships its own types).
  
  Sidebar gating and the Settings page already read config.features directly
  and are unchanged. The <Flags> render component was never consumed, so the
  useFeature/<Feature>/withFeature API is available but not yet adopted.
  Behavior is fully preserved (54 web-client tests green). Unrelated to the
  CloudFormation Enable* feature flags used by IPA stacks.
- **web-client** — Collapse sidebar to an icon rail, not offcanvas

  Recorded retroactively for the same reason as the preceding commits.
  
  The left nav moved from collapsible="offcanvas" to collapsible="icon",
  so toggling shrinks the sidebar to a 3rem square-icon strip (the
  Slack, Linear and VS Code pattern) rather than sliding it off-screen
  entirely. The brand row collapses to its icon, group labels and the
  version badge hide, and every nav item gained a hover tooltip so the
  bare icons stay identifiable while collapsed.


### Documentation
- Add SECURITY.md and not-production-ready notice in README

  Add a SECURITY.md documenting that samples are proof-of-value
  demonstrations, not production-ready, with no guaranteed ongoing
  patches, plus vulnerability reporting guidance. Add a matching
  disclaimer callout near the top of the README linking to it.
- **infra** — Document the Kubernetes local loop and path to production

  Recorded retroactively for the same reason as the preceding commits.
  
  Adds developer-docs/infra/kubernetes.md (chart, Tiltfile, ctlptl and
  Makefile internals, mirroring terraform.md) and
  developer-docs/infra/kubernetes-tools.md (optional non-IPA community
  CLIs -- k9s, kubectx/kubens, kftray, stern -- install links only, not
  checked by `make doctor`). Adds builder guides
  guides/kubernetes-local-development.md and
  guides/kubernetes-path-to-production.md. Both guides, plus
  infra/k8s/README.md, carry a Future Work section recording the
  deferred cloud-cluster path: CFN/TF cluster provisioning, ECR wiring,
  IRSA role creation, a CodePipeline helm upgrade --install stage, Local
  IRSA, and ingress templates. None of that was built this round.
  Agent-context CLAUDE.md files were added across
  infra/containers/rest-k8s/, infra/k8s/, the chart itself, and eks/.


### Fixed
- **ci** — Harden supply chain — pin actions to SHAs, add dep cooldowns

  Repairs the 4 unsuppressed High-severity supply-chain SAST rule classes
  (28 findings) surfaced by ASH, all via code fixes with no new suppressions:
  
  - Pin all 12 GitHub Actions `uses:` refs across deploy-docs, release, and
    security-compliance workflows to full 40-char commit SHAs with `# vX.Y.Z`
    comments (github-actions-mutable-action-tag ×22).
  - Replace the TruffleHog `curl -sSfL … | sh` installer in the ferret-scan
    job with the SHA-pinned trufflesecurity/trufflehog action, preserving the
    full-history scan + --fail semantics (gha-curl-pipe-shell ×2).
  - Add pnpm/npm install cooldown to docs/.npmrc: minimumReleaseAge=1440
    (pnpm) and min-release-age=7 (npm) (npm-missing-minimum-release-age ×2).
  - Add exclude-newer = "7 days" under [tool.uv] and re-lock app-lib/uv.lock;
    floor-pin constraints held, 71 tests pass (uv-missing-dependency-cooldown ×2).
  
  Local ASH re-scan confirms all four rule classes report zero findings;
  .ash/ash.yaml is untouched (271 existing suppressions preserved).
- **app-lib** — Enable Jinja2 autoescape unconditionally

  ACAT Jinja2AutoescapeDisabled (finding 696d75fe-28f5-4104-9c53-3e6fc7a65203)
  flagged the FileSystemLoader Environment: select_autoescape(["html","xml"])
  leaves autoescape OFF for any other extension, and the string-render path had
  no autoescape at all. Set autoescape=True on both Environments so HTML content
  is always escaped, mitigating XSS.
- **infra** — Raise GITHUB_DEPLOY_KEY length floor from 200 to 350 bytes

  Addresses the critical finding from the amazon-q review on MR !5.
  
  The smallest key type this would ever hold is an OpenSSH ed25519 private key,
  which measures 387 bytes — so a 200-byte floor accepted a key truncated to
  roughly half its length and passed it to ssh-add. Verified: a 200-byte
  truncation cleared the old check, and an 83-byte public key would have too.
  
  The threshold exists to catch a mis-pasted or clipped CI variable before ssh-add
  fails with something less obvious, so it belongs just under the smallest
  legitimate key rather than far below it. Also adds a hint naming the two
  realistic causes — a truncated paste, or the public key pasted instead of the
  private one.

## [0.1.7] - 2026-06-09

### Documentation
- Changelog entry for deploy→deploy wiring fix
- **ipa** — Document buildspec YAML brace pitfall in codepipeline skill

  A bare `{ ... }` in a CodeBuild buildspec command scalar parses as a YAML
  flow mapping, which CodeBuild rejects with YAML_FILE_ERROR at
  DOWNLOAD_SOURCE. Add an authoring rule to SKILL.md showing the safe
  block-scalar form, and add the failure mode (with recovery) to the
  TROUBLESHOOT failure catalog so future regenerations of the skill don't
  reintroduce the bug.
- **ipa** — Document CORS preflight pattern for terraform backend

  The TF backend module uses a \$default catch-all route which intercepts
  OPTIONS preflight requests and routes them through the JWT authorizer,
  breaking browser CORS. The fix is an explicit OPTIONS /{proxy+} route
  with authorization_type=NONE that lets preflight reach the Lambda's
  CORSMiddleware.
  
  Add inline comment in main.tf and a CORS Preflight Handling section in
  the stack skill so the pattern is preserved when authoring or
  regenerating the backend stack.


### Fixed
- **ipa** — Split deploy.mk wiring rules by source lifecycle

  Make parses `-include .env` once at process startup, so values that
  env.mk writes to .env mid-run (after one deploy target completes) are
  invisible to subsequent targets in the same Make invocation. This
  broke deploy→deploy wiring such as queue.QueueArn → backend.SqsSendQueueArns,
  which produced an empty parameter and a CREATE_FAILED LambdaExecutionRole
  when IAM rejected an empty Resource list.
  
  Update MAKEFILE_TEMPLATES.md to specify two cases:
  - Case A: prepare-source wiring keeps reading from .env via $(VAR)
  - Case B: deploy-source wiring captures via $(eval ... describe-stacks ...)
    at the top of the target, stored as {VAR}_LIVE
  
  Document the rationale (env.mk works across Make invocations, not within
  one) and flag the same-lifecycle wiring on backend SqsQueueUrl /
  SqsSendQueueArns parameters in the stack skill.
- **infra** — Upgrade CodeBuild image to standard:8.0 for Node 20+

  The web-client build (vite 7, @tailwindcss/oxide) requires Node 20.19+.
  standard:7.0 ships Node 18, which fails with EBADENGINE warnings and a
  fatal "Cannot find native binding" from oxide. standard:8.0 ships Node
  22 natively.
  
  Update both the terraform default and the codepipeline skill so a future
  regeneration picks up the new image.
- **infra** — Install uv in CodeBuild and harden buildspec preflight

  post-deploy.mk and build.mk invoke `uv run python ...`, but the
  standard:8.0 image does not include uv. Install it via the official
  astral.sh installer and copy the binary to /usr/local/bin so it is on
  PATH for every subsequent shell (CodeBuild starts a fresh shell per
  command). Also rewrite the terraform-presence guard as a block scalar
  to avoid the YAML brace pitfall, and add a parallel uv-presence guard
  to the pre_build phase. Update SKILL.md and TROUBLESHOOT.md so a future
  regeneration of the codepipeline stack carries these fixes.
- **ipa** — Pass --all-extras to uv run for load-data

  uv run re-syncs the project venv to default deps (base + dev) before
  executing, which removed pynamodb (declared in the rest/api_lambda/all
  optional extras) and broke the post-deploy load-data step in CodePipeline.
  Update the ipa-compose template so regenerated post-deploy.mk preserves
  --all-extras on the load_dynamodb_util invocation.
- **infra** — Use underscores in passengers DynamoDB table name

  The Terraform backend module created the passengers table as
  ${namespace}-${environment}-passengers (hyphens), while the CFN
  template, app-lib's PynamodbUtil, and the documented naming contract
  in infra/cfn/backend/CLAUDE.md all use underscores. The mismatch
  caused the post-deploy load-data step to fail with
  ResourceNotFoundException on table app_dev_passengers.
  
  Switch the Terraform name to ${namespace}_${environment}_passengers
  so all three sources of truth agree. On next apply Terraform will
  recreate the table; the table held only seed data so loss is
  acceptable.
- **infra** — Align passengers table hash key with PynamoDB model

  Terraform created the passengers table with hash key PassengerId (N),
  but the PynamoDB model and CFN backend template both use id (S). The
  mismatch caused load-data to fail with ValidationException 'Missing
  the key PassengerId in the item' once the table existed.
  
  Change Terraform to hash_key=id, type=S so all three sources agree
  (model, CFN, Terraform). On next apply Terraform recreates the table;
  seed data only, no loss concern.
- **infra** — Rebuild frontend in PostDeploy if cross-stage artifact missing

  The pipeline relies on the Build stage's BuildOutput artifact to deliver
  web-client/dist/ into the PostDeploy stage's working directory. The
  existing pre_build copy is silently skipped when CODEBUILD_SRC_DIR_BuildOutput
  is unset or missing the dist/ subtree, leading post-deploy configure-frontend
  to fail with 'web-client/dist/index.html not found'.
  
  Add an explicit check + fallback: when running post-deploy.mk and dist/
  is missing, rebuild it from source (npm ci && npm run build). Adds ~30s
  to PostDeploy in the worst case; eliminates the cross-stage artifact
  dependency as a failure mode.
- **ipa** — Add ensure-frontend-dist step to compose template

  Encode a permanent fallback in the compose template so generated
  post-deploy.mk rebuilds web-client/dist/ when the cross-stage CodeBuild
  artifact does not deliver it to PostDeploy. Pairs with the buildspec
  fallback added in 015f500 — defense in depth across infra and the
  generated Makefile.
- **infra** — Add uv sync and frontend rebuild to codepipeline buildspec

  The Terraform codepipeline buildspec lacked two things:
  1. `uv sync --all-extras` — post-deploy's load-data step needs pynamodb
     which lives in optional extras. Without this, every CodeBuild run that
     hits post-deploy.mk fails with ModuleNotFoundError.
  2. Frontend rebuild fallback — when IPA_MAKEFILE=post-deploy.mk and
     web-client/dist/index.html is missing (cross-stage artifact not
     delivered), rebuild it from source via npm ci && npm run build.
  
  Both are gated so they only run when relevant (load-data always needs
  extras; frontend rebuild only fires in PostDeploy when dist is absent).
- **infra** — Align Terraform/CFN drift — naming contract + cognito username

  Three drifts where the Terraform modules diverged from CFN templates and
  the documented naming contract:
  
  1. tfstate-lock DynamoDB table: hyphens→underscores in CFN and skill doc
     (matches the {ns}_{env}_{suffix} contract used by passengers/jobs).
  2. jobs DynamoDB table (queue tier TF): hyphens→underscores in the table
     name. Same fix pattern as the earlier passengers table fix.
  3. Cognito user pool (TF): drop `username_attributes = ["email"]`. CFN
     doesn't set this, so the documented behavior is "username is a
     standalone string, email is a separate verified attribute". The TF
     override forced username-as-email and broke admin-create flows that
     pass a non-email username.
- **infra** — Replace bare-brace shell expression in codepipeline buildspec

  YAML parsed `command -v terraform || { echo ...; exit 1; }` as a flow
  mapping, failing CodeBuild at DOWNLOAD_SOURCE with YAML_FILE_ERROR.
  Rewrite as a block-scalar if/then/fi (matches the TF module pattern).
  
  Add a compliance grep check to the codepipeline skill so future template
  edits surface bare-brace regressions before commit.
- **infra** — Apply env.mk two-invocation bootstrap to inline buildspec

  The CodeBuild buildspec inside codepipeline.yml ran a single
  `make -f scripts/env.mk update-env`, which leaves ECR_REPO_URI and
  other Terraform-derived values empty: TF_BACKEND_CONFIG resolves at
  Make parse time, before update-env-tfstate writes TF_STATE_BUCKET to
  .env, so every Terraform-based update-env-* target silently fails.
  Symptom: `docker tag app-dev-rest-lambda :0.1.0-<sha>` — empty repo
  URI, invalid reference, build.mk fails.
  
  The two-invocation pattern was added to MAKEFILE_TEMPLATES.md in
  4e0057f but the inline buildspec was missed because it lives frozen
  in the CFN template and is not regenerated by /ipa-compose. Add a
  cross-reference note in MAKEFILE_TEMPLATES.md so future edits to the
  bootstrap pattern propagate to the buildspec.
- **ipa** — Use terraform output -json|jq for safe env.mk capture

  terraform output -raw writes "Warning: No outputs found" to stdout
  when state has no value, exiting 0. The captured warning text lands
  verbatim in .env, breaking GNU Make's parser ("missing separator").
  
  Replace per-target raw-output captures with a tf_output helper that
  uses output -json | jq | tr -d '\n\r' — returns the raw value if
  present, empty if absent, no warning leakage.
  
  Also assert jq presence in the codepipeline buildspec install phase,
  mirroring the existing terraform/uv assertions.
- **infra** — Bring terraform modules to parity with cloudformation

  Terraform modules were missing critical configuration that CloudFormation
  counterparts include, causing deployed apps to fail at runtime: jobs
  feature returned 503, auth/CORS env vars were unset, and the cognito
  custom domain lacked Managed Login v2.
  
  - queue: fix dynamodb jobs hash key (JobId -> id) to match PynamoDB
    model; add AUTH_ISSUER, AUTH_AUDIENCE env vars; rename INVOKE_MODE to
    APP_INVOKE_MODE; add reserved concurrency (10); add ECR pull, Bedrock,
    and cross-tier passengers IAM policies; add sqs:ChangeMessageVisibility;
    set batch_size=1 with no batching window
  - backend: add AUTH_ISSUER, AUTH_AUDIENCE, CORS_ALLOWED_ORIGINS, and
    AWS_LWA_REMOVE_BASE_PATH env vars; rename INVOKE_MODE to
    APP_INVOKE_MODE; add reserved concurrency (50); add ECR pull, Bedrock,
    and cross-tier jobs IAM policies
  - cognito: add Managed Login v2 branding resource and managed_login_version
    on domain; add ALLOW_USER_PASSWORD_AUTH; add localhost callback and
    logout URLs; add explicit token validity (8h access/id, 24h refresh);
    add hosted_ui_url output
  - frontend: add DenyInsecureTransport bucket policy statement; add S3
    access logging to logs bucket; set http_version=http2and3; add
    error_caching_min_ttl=0 on custom error responses
  - logs: add AllowS3ServerAccessLogs and AllowVPCFlowLogs bucket policy
    statements; add conditional KMS encryption via kms_key_arn variable
- **infra** — Add OPTIONS route to bypass JWT authorizer for CORS preflight

  API GW v2's $default route intercepts OPTIONS preflight requests and
  routes them through the JWT authorizer, which rejects them (no Bearer
  token on preflight). This causes CORS failures in the browser.
  
  Add an explicit OPTIONS /{proxy+} route with authorization_type=NONE
  so preflight requests reach the Lambda where FastAPI CORSMiddleware
  handles them correctly.

## [0.1.6] - 2026-05-18

### Added
- Implement /ipa.init skill for project configuration

  Add the IPA init skill that interactively configures a project's .env
  file with 7 IPA-managed variables (AWS_PROFILE, AWS_REGION,
  AWS_ACCOUNT_ID, IPA_NAMESPACE, IPA_ENV, IPA_CODE_AGENT, IPA_IAC).
  
  Includes first-time init with auto-detection, idempotent re-init with
  selective updates, .env.example generation, validation rules, and
  edge case handling.


### CI/Build
- Combine auto-tag and github-release into single job; strip internal/ from Pages

  Combined auto-tag and github-release into auto-tag-and-release. Separate jobs
  were unreliable because CI_JOB_TOKEN-authenticated tag pushes do not trigger
  follow-up tag pipelines, so the tag-driven github-release job never ran on
  v0.1.3 or v0.1.4 — both had to be pushed to GitHub manually.
  
  Pages job now removes docs/docs/developer-docs/internal/ before the Docusaurus
  build so internal docs do not publish to GitLab Pages, mirroring the GitHub
  release filter in scripts/util/github-push.sh.
  
  Moves the corresponding CHANGELOG entry from [0.1.4] (where it was inaccurate
  — never actually shipped) to [Unreleased] for the next release.
- Full clone for tag-and-release to fix GitHub mirror push

  The github-push.sh job amends the release commit and force-pushes to the
  GitHub mirror. With GitLab's default shallow clone (depth=20), git's pack
  negotiation references ancestor objects past the shallow boundary once
  release history exceeds that window, and GitHub rejects the push with
  "did not receive expected object <sha>". Setting GIT_DEPTH: "0" gives the
  job a full clone so the pack is self-contained.


### Changed
- **ipa** — Make env.mk the canonical stack-output bridge

  Single rule: all CloudFormation stack outputs flow through scripts/env.mk
  into .env, and every consumer (deploy.mk, post-deploy.mk, local dev
  server) reads from .env via -include. No consumer calls describe-stacks
  directly anymore. prepare.mk keeps describe-stacks for the bootstrap
  case where env.mk does not yet exist on a fresh project.
  
  In CodeBuild, each stage runs `make -f scripts/env.mk update-env` as
  its prelude before the main IPA target. Containers do not share state
  between stages, so each stage starts with a fresh container, queries
  live stacks, writes .env, and runs its target. test.mk is skipped.
  
  Stack outputs are no longer baked into CodeBuild EnvironmentVariables
  (ECR_REPO_URI, OIDC_*) — those values could go stale and silently
  override live values via Make's environment-precedence rule. Only
  orchestration/identity values stay in EnvironmentVariables.
  
  The env.mk Cognito target now captures COGNITO_DOMAIN_PREFIX from the
  live CognitoDomain stack output. update-cognito-callback reads this
  deployed value instead of recomputing $(APP_NAMESPACE)-$(APP_ENV)-
  $(APP_ACCOUNT_HASH), which prevents parameter drift on the immutable
  AWS::Cognito::UserPoolDomain resource — drift was triggering REPLACE
  which destroyed the live domain mid-update.
  
  This refactor also generalizes the LOG_BUCKET_NAME fix (no special-case
  $(eval) in deploy-frontend) and uplifts the SQS wiring pattern from
  per-target $(eval) to the same env.mk-driven path as OIDC and ECR.
  
  Files changed:
  - .claude/skills/ipa-compose/MAKEFILE_TEMPLATES.md — variable-resolution
    convention rewritten; env.mk extended with backend/frontend/cognito-
    domain captures; deploy/post-deploy patterns drop $(eval); buildspec
    prelude documented.
  - .claude/skills/ipa-stack-codepipeline/SKILL.md — wirable parameters
    and CodeBuild env vars updated to match.
  - infra/cfn/codepipeline/codepipeline.yml — buildspec prelude added;
    EcrRepoUri/OidcIssuer/OidcClientId/OidcEndSessionEndpoint parameters
    removed; corresponding CodeBuild EnvironmentVariables removed.
  - CHANGELOG.md — entry under [0.1.6].
  
  Generated Makefiles (scripts/*.mk) are gitignored on main and will be
  regenerated by /ipa-compose on the install branch.


### Documentation
- Derive baseUrl from CI_PAGES_URL to track GitLab project slug
- **internal** — Expose internal section on GitLab Pages with conditional repo link

  Internal docs (developer-docs/internal/) now publish to GitLab Pages
  since that site is internal-only. They remain filtered from the GitHub
  mirror via scripts/util/github-push.sh EXCLUDE_PATHS.
  
  Renamed operations/{README,runbooks/README} to index.md to match the
  published-section convention and added sidebar_label so the sidebar
  shows distinct names instead of nested "Overview" entries.
  
  Conditional navbar repo link: GitLab icon -> code.aws.dev when
  DOCS_TARGET is unset; GitHub icon -> aws-samples/sample-innovation-patterns
  when DOCS_TARGET=github.


### Fixed
- **web-client** — Regenerate lockfile with cross-platform native binaries

  The prior swc fix only addressed @swc/core binaries. CodeBuild npm ci
  was still failing on missing Linux variants for @rollup/rollup-*,
  @esbuild/*, @tailwindcss/oxide-*, and lightningcss-* — all of which
  ship platform-specific optionalDependencies that npm omits from the
  lockfile when installed on macOS.
  
  Regenerated web-client/package-lock.json with both linux-x64 and
  darwin-arm64 platform entries. Verified with npm ci --os=linux --cpu=x64
  (simulating CodeBuild) and local npm run build on darwin-arm64.
- **infra** — Allow cloudwatch:* in innovation builder policy for tier stack alarms

  Tier stacks that declare AWS::CloudWatch::Alarm or
  AWS::CloudWatch::Dashboard resources (queue, backend) failed on
  cloudwatch:PutDashboard / cloudwatch:PutMetricAlarm AccessDenied
  because InnovationBuilderPolicy granted logs:* but nothing in the
  cloudwatch: namespace — the two are separate IAM namespaces.
  
  Destructive ops (DeleteAlarms, DeleteDashboards, DisableAlarmActions)
  remain explicitly denied by SecureLoggingConfigs in both the boundary
  and the identity policy, so the broad allow follows the template's
  existing pattern (broad allow + targeted deny).
- **ipa** — Generate deploy-frontend with $(eval) for log bucket name

  Update MAKEFILE_TEMPLATES.md so future /ipa-compose runs emit
  $(eval LOG_BUCKET_NAME_VAL := $(shell aws cloudformation describe-stacks ...))
  in deploy targets that wire from the logs prepare stack, instead of
  reading $(LOG_BUCKET_NAME) directly from .env.

## [0.1.4] - 2026-05-13

### Added

- **`/ipa-stack-logs`** — new prepare-lifecycle stack for a centralized S3 log bucket (CloudFront, S3 access, VPC flow logs). Composed via `/ipa-compose` and auto-included as a transitive dependency when a downstream stack wires `LogBucketName`. Generates `update-env-logs` env.mk target and a `prepare.mk` teardown note for non-empty buckets.

### Changed

- **`/ipa-security`** — log bucket extracted from the security stack into the new `/ipa-stack-logs` prepare stack. `/ipa-security` now provisions only IAM roles (one CloudFormation stack instead of two). The frontend tier's `LogBucketDomainName` parameter now sources from `logs` instead of `security`.
- **`/ipa-compose`** — recursive auto-include now resolves `logs` alongside `cognito`/`ecr`/`codecommit`. Generated deploy targets that reference `$(LOG_BUCKET_NAME)` now emit a pre-check that validates the `{ns}-{env}-logs` stack exists before deploying.

### Fixed

- **Docs site** — Docusaurus `baseUrl` now derives from `CI_PAGES_URL` so the GitLab Pages deploy tracks the project slug instead of a hardcoded path.

## [0.1.3] - 2026-05-12

### Changed

- **Compose CodePipeline** — integrated `codecommit` and `codepipeline` as composable prepare-lifecycle stacks in `/ipa-compose`. Added `## Stack Identity`, `## Wirable Parameters`, `## Compose Config`, and `## Deploy Order` to both stack skills. Compose auto-includes `codecommit` as a transitive dependency of `codepipeline`, prompts for repository name and source branch, and generates `prepare.mk` targets with full cross-stack wiring. Added `update-env-pipeline` target to env.mk generation.

### Deprecated

- **`/ipa-codepipeline`** — replaced with the standard compose+prepare flow (`/ipa-compose codepipeline` → `/ipa-prepare`). Existing deployments are compatible; re-compose to align.

## [0.1.2] - 2026-05-11

### Changed

- **Lifecycle refactor** — collapsed 5-skill lifecycle into 4-step flow: `/ipa-init` → `/ipa-compose` → `/ipa-prepare` → `/ipa-deploy`. `/ipa-security` is now embedded in `/ipa-compose` (triggered on first compose) and supports three paths: existing role ARN, managed policy, or the new Innovation Builder Stack (recommended — permissions boundary + 47-service policy + four scoped roles). `/ipa-compose` auto-runs `/ipa-init` when `.env` is missing; `/ipa-deploy` hard-gates on prepare stacks instead of auto-triggering. Split `infra/cfn/generated/security.yml` into `iam.yml` + `log-bucket.yml`.
- **Skill naming** — renamed all `ipa.*` skills to use `-` as the separator instead of `.` (e.g., `/ipa.compose` → `/ipa-compose`, `/ipa.stack.backend` → `/ipa-stack-backend`). Affects 17 skill directories, frontmatter, internal references, and all published documentation.

### Added

- **`/ipa-help`** — new diagnostic skill that reports IPA project state and suggests the next lifecycle skill to run. Read-only; does not invoke other skills.
- **Innovation Builder Security stack** — new single-template CloudFormation stack at `infra/cfn/security/innovation-builder-security.yml` consolidating the IAM policy + permissions boundary, CodeBuild role, SageMaker execution role, builder role, and EC2 builder role into one deployable artifact. Consumed as-is by `/ipa-security`; deploy this OR the per-resource templates, not both.
- **`/ipa-security` skill** — full implementation supporting three setup paths (existing role ARN, AWS managed policy, or the Innovation Builder Stack), with deploy/update/review flows, `.env` wiring for `DEPLOYMENT_ROLE_ARN`/`PERMISSIONS_BOUNDARY_ARN`, and stack drift handling.

### Removed

- **`/ipa-quickstart`** — removed; the 4-step lifecycle is the new quickstart.

## [0.1.1] - 2026-04-26

### Changed

- **Docs site** — GitHub Pages now deploys on pushes to `main` instead of release tags, matching the existing GitLab Pages trigger and avoiding the `github-pages` environment protection rule that blocks tag-based deploys.

### Fixed

- **Release pipeline** — `github-push.sh` now sets a local committer identity before amending the filtered release commit, preventing `fatal: unable to auto-detect email address` in CI.
- **Release pipeline** — after amending the release commit to strip internal-only paths, the release tag is now moved to the amended commit so GitHub's tag, `main`, and auto-generated release tarball all reference the same filtered tree.
- **Auto-tag** — rule no longer excludes `$CI_PIPELINE_SOURCE == "push"`, which was blocking the job from ever firing on a standard push-to-main. Tag existence now checked against `origin` to tolerate CI's shallow clone.

## [0.1.0] - 2026-04-26

### Added

- **IPA Skills Framework** — composable Claude Code skills for AWS infrastructure deployment
  - Lifecycle skills: `/ipa.init`, `/ipa.security`, `/ipa.compose`, `/ipa.prepare`, `/ipa.deploy`, `/ipa.destroy`
  - Authoring skills: `/ipa.author.stack`, `/ipa.author.guide`
  - CI/CD skill: `/ipa.codepipeline`
- **Tier Stacks** — consolidated CloudFormation templates for serverless applications
  - Backend tier: Lambda + API Gateway v2 + DynamoDB + CloudWatch
  - Frontend tier: S3 + CloudFront + OAC
  - Queue tier: SQS + DLQ + worker Lambda + ESM + DynamoDB + CloudWatch
- **Prepare Stacks** — one-time prerequisite infrastructure
  - Cognito User Pool with OAuth 2.0 Hosted UI
  - ECR repository for container images
- **Patterns** — composable solution templates
  - `react-rest-lambda` — full-stack serverless web application
  - `sqs-lambda` — background job processing (compose-only, layers onto base pattern)
- **Application Library (`app-lib/`)** — Python 3.12 library with FastAPI, PynamoDB, JWT auth, and feature-centric module architecture
- **Web Client (`web-client/`)** — React 19 + TypeScript SPA with RTK Query, Cognito OIDC, and OpenAPI codegen pipeline
- **Documentation Site** — Docusaurus 3 with autogenerated sidebars, Mermaid diagrams, and local-only working section
- **Security** — ASH integration in GitLab CI, least-privilege IAM, encryption by default
- **Generated Makefiles** — plain GNU Make with inline `aws` CLI calls; no runtime dependency on IPA

