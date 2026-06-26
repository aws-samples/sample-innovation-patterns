---
name: ipa-k8s-help
description: "Guide and troubleshoot the local Kubernetes (k3d + Helm + Tilt)
  inner-dev loop, and guide a manual EKS deploy of the app-lib chart. Use when
  the user says 'set up local k8s', 'tilt won't start', 'pod can't reach
  DynamoDB', 'my local cluster is broken', 'deploy this chart to EKS', or
  invokes /ipa-k8s-help. NOT for IPA lifecycle state — that is /ipa-help."
model: opus
---

# /ipa-k8s-help — Kubernetes Setup & Troubleshooting Guide

This skill is the interactive counterpart to `make doctor`. It helps a builder
stand up and debug the **local** k3d/Tilt inner-dev loop for the `app-lib`
service, and it **guides** (does not perform) a **manual EKS** deploy of the
Helm chart.

**This is a guidance/helper skill, not a stack skill** — it wraps no
CloudFormation contract and composes nothing.

## /ipa-k8s-help vs /ipa-help

- **`/ipa-help`** reports IPA *lifecycle* state (init → compose → prepare →
  deploy) and suggests the next lifecycle skill. It is about CloudFormation
  tiers.
- **`/ipa-k8s-help`** (this skill) is about the *Kubernetes* offering: the local
  Tilt loop and the manual EKS path. It checks tools and configuration and
  guides; it is not a lifecycle inspector.

## Iron rules (never violate)

- **Check and instruct only.** NEVER auto-install a tool. NEVER run
  `ctlptl apply`, `tilt up`, `helm install/upgrade`, or `kubectl apply` on the
  builder's behalf. Print the exact command and let the builder run it.
- **Read-only diagnostics.** You may run read-only checks (`command -v`,
  `aws sts get-caller-identity`, `aws dynamodb describe-table`,
  `kubectl config current-context`, `helm template`). You may NOT mutate any
  cluster or cloud resource.
- **Missing `.env` is a first-class failure** — never assume it exists.
- **Degrade gracefully.** When a cloud resource is unreachable, report "cannot
  verify" and say why; do not fail the whole flow.

---

## Scope A — Local loop (k3d + Helm + Tilt)

Work through these steps in order. Stop at the first failure, print the exact
remediation, and re-run from that step once the builder reports it fixed.

### Step 1 — Tool check

Run `command -v docker kubectl helm k3d tilt ctlptl aws`. For each missing tool,
name it and print the exact install command:

| Tool | Install |
|---|---|
| docker | https://docs.docker.com/get-docker/ |
| kubectl | `brew install kubectl` |
| helm | `brew install helm` |
| k3d | `brew install k3d` |
| tilt | `brew install tilt-dev/tap/tilt` |
| ctlptl | `brew install tilt-dev/tap/ctlptl` |
| aws | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |

Do not proceed to Step 2 until every tool is present. (This mirrors
`make doctor`; either is a valid gate.)

### Step 2 — Credentials check

- If the repo-root `.env` is **absent**, STOP: report a first-class "missing
  `.env`" failure and instruct the builder to run `/ipa-init` (or copy
  `.env.example`). Do not assume defaults.
- Otherwise run `set -a; . ./.env; set +a; aws sts get-caller-identity`. On
  failure (expired SSO, wrong profile), print the error and the fix:
  `aws sso login` (or `aws configure`), then re-run.

### Step 3 — Convergence check

The local pod must read the SAME DynamoDB table the backend tier created. Read
`APP_NAMESPACE`, `APP_ENV`, `AWS_REGION` from `.env`. Confirm they are non-empty
and tell the builder the table name the pod will resolve:
`{APP_NAMESPACE}_{APP_ENV}_passengers`. These are injected by the Tiltfile from
`.env` — the builder should NOT hand-edit the overlay to set them.

### Step 4 — Table-exists check

Run `aws dynamodb describe-table --table-name {APP_NAMESPACE}_{APP_ENV}_passengers
--region {AWS_REGION}`. If it does not exist, the data plane is not deployed:
instruct the builder to run `/ipa-compose → /ipa-prepare → /ipa-deploy` for the
backend tier with `EnablePassengersTable=true`. If the call is AccessDenied,
their profile lacks DynamoDB read on that table.

### Step 5 — Cluster state

Run `kubectl config current-context`. If it is not the local k3d context
(`k3d-k3d-ipa-local`), the cluster is not set up: instruct `make local-setup`.
If `ctlptl get cluster` shows no cluster, same remedy.

### Step 6 — Guided run

Walk the builder through, one command at a time (they run each):

1. `make local-setup` — creates the k3d cluster + registry.
2. `make local-up` — Tilt builds, deploys, port-forwards :8000.
3. Verify: `curl -s localhost:8000/health` → `{"status":"ok"}`.
4. Tear down when done: `make local-destroy`.

### Step 7 — Triage table

| Symptom | Likely cause | Remediation (builder runs) |
|---|---|---|
| `make doctor` names a missing CLI | tool not installed | run the printed install command |
| missing `.env` | not initialized | `/ipa-init` (or copy `.env.example`) |
| `aws-check-creds` red in Tilt | expired/absent SSO session | `aws sso login`, then re-trigger |
| port 8000 already bound | another process on :8000 | `lsof -i :8000` then free it, or change the port-forward |
| pod `ResourceNotFoundException` | table not deployed / name mismatch | Step 4; confirm `.env` matches the deployed tier |
| pod `AccessDeniedException` | profile lacks DynamoDB read | grant read on `{ns}_{env}_passengers`, or switch profile |
| `kubectl` context wrong | pointed at another cluster | `kubectl config use-context k3d-k3d-ipa-local` |
| live-update not syncing | edited outside `app-lib/src/app_lib` | edit under the synced path, or expect a rebuild |
| cluster won't create | docker not running | start Docker Desktop, re-run `make local-setup` |

---

## Scope B — Manual EKS deploy (guidance only)

For a cloud deploy, **walk the builder through the annotated overlay and validate
pre-conditions — apply nothing.** The authoritative guidance lives in
`infra/k8s/envs/eks/CLAUDE.md`; **reference that file** rather than restating its
steps here (single source — avoids drift).

What to do:

1. Open `infra/k8s/envs/eks/values.yaml` and walk each override point with the
   builder (ECR image URI, IRSA role ARN, namespace/region env, replicas,
   resources). Point them at `eks/README.md` (copy-and-customize) and
   `eks/CLAUDE.md` (the guidance + review checklist).
2. Validate the pre-conditions from `eks/CLAUDE.md` using read-only checks only:
   credentials, target `kubectl` context (must NOT be the local k3d cluster),
   ECR repo + pushed image, IRSA role exists with a scoped trust + DynamoDB
   policy, and convergence env resolves to the intended table.
3. Render for inspection (does not deploy):
   `helm template app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/eks/values.yaml`.
4. Hand the deploy command to the builder to run themselves:
   `helm upgrade --install app-lib infra/k8s/helm/app-lib -f <their-values>`.
   You do not run it.

**Degrade gracefully:** if a cloud resource is unreachable (no cluster access,
ECR not reachable), report exactly what you could not verify and continue with
what you can. EKS-scope behavior is not verifiable without a real cluster.

---

## What this skill does NOT do

- Does not install any tool.
- Does not create, apply, or modify any cluster or cloud resource.
- Does not run `make local-up`, `tilt up`, `ctlptl apply`, or any `helm`/
  `kubectl` apply for the builder.
- Does not report IPA lifecycle state — that is `/ipa-help`.
