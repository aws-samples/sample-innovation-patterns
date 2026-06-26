---
title: Kubernetes Local Development
sidebar_position: 11
---

# Kubernetes Local Development

## Overview

This guide stands up a local Kubernetes inner-dev loop for the `app-lib` FastAPI
service using k3d, Helm, and Tilt. By the end, the service is running in a local
k3d cluster, reachable at `http://localhost:8000`, with live-reload on source
edits and reading a **real, AWS-deployed** DynamoDB table through your own
`~/.aws` credentials.

## When to Use This Guide

Use this guide when you want to develop `app-lib` against Kubernetes locally —
to iterate on the service the way it will run in a cluster, rather than as a
Lambda or a bare `uvicorn` process. It is the Kubernetes counterpart to the
[Local Development](./local-development.md) guide.

Do **not** use this guide to deploy to a real cluster. For the cloud path see
[Kubernetes Path to Production](./kubernetes-path-to-production.md).

## Before You Start

Install these command-line tools (this guide does not install them for you):

| Tool | Purpose | Install |
|---|---|---|
| docker | Container runtime | https://docs.docker.com/get-docker/ |
| kubectl | Kubernetes CLI | `brew install kubectl` |
| helm | Chart deploys | `brew install helm` |
| k3d | Local k3s-in-Docker cluster | `brew install k3d` |
| tilt | Inner-dev-loop driver | `brew install tilt-dev/tap/tilt` |
| ctlptl | Cluster + registry manager | `brew install tilt-dev/tap/ctlptl` |
| AWS CLI v2 | Credentials + DynamoDB checks | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |

`make doctor` checks all of these and prints the exact install command for any
that are missing. The interactive `/ipa-k8s-help` skill does the same and triages
failures.

:::note Split-plane precondition
The local pod reads a **real deployed** DynamoDB table — it does not run its own
database. Before starting, deploy the data plane with the existing flow:
`/ipa-compose → /ipa-prepare → /ipa-deploy` for the **backend tier** with
`EnablePassengersTable=true`. The pod and the table converge on the name
`{APP_NAMESPACE}_{APP_ENV}_passengers`, built from the same `.env` values on
both sides.
:::

:::warning Host credentials reach the pod
The local loop mounts your `~/.aws` directory into the pod so it can call AWS
with **your full IAM identity**. This is a deliberate POC trade-off — the
credentials are your own, mounted at runtime, never embedded in the chart, image,
or `.env`. Do not use this credential model in a cluster; the cloud path uses
scoped IRSA roles instead.
:::

## Before / Target State

**Before:** `app-lib` runs only as a Lambda image or a local `uvicorn` process;
no local cluster exists. The DynamoDB table is deployed in AWS.

**Target:** A k3d cluster runs the `app-lib` pod, reachable at
`localhost:8000`, live-reloading on source edits, and serving rows from the real
deployed table.

## Steps

1. **Check tools.** From the repo root:

   ```bash
   make doctor
   ```

   Fix any tool it names before continuing. It never installs anything.

2. **Create the cluster.** This creates the k3d cluster and local registry and
   maps `${HOME}/.aws` into the cluster nodes:

   ```bash
   make local-setup
   ```

3. **Start the loop.** Tilt builds the image, deploys the chart, verifies your
   AWS credentials, and port-forwards `:8000`:

   ```bash
   make local-up
   ```

   Leave this running. The Tilt UI (printed in the output) shows resource
   status; the `aws-check-creds` resource must be green before the pod starts.

4. **Iterate.** Edit any file under `app-lib/src/app_lib/`. Tilt live-syncs the
   change and restarts `uvicorn` in place — no full image rebuild.

5. **Tear down** when finished:

   ```bash
   make local-destroy
   ```

## Verification

With the loop running:

```bash
curl -s localhost:8000/health      # -> {"status":"ok"}
curl -s localhost:8000/api/v1/passengers   # -> rows from the real deployed table
```

The first confirms the pod is up; the second confirms the split-plane read
against the deployed DynamoDB table succeeded.

## Troubleshooting

For interactive, step-by-step diagnosis, run `/ipa-k8s-help`. Common failures:

| Symptom | Cause | Fix |
|---|---|---|
| `make doctor` names a missing tool | not installed | run the printed install command |
| `aws-check-creds` red in Tilt | expired SSO session | `aws sso login`, then re-trigger the resource |
| port 8000 already in use | another process bound :8000 | `lsof -i :8000`, free it, re-run |
| pod `ResourceNotFoundException` | table not deployed or name mismatch | deploy the backend tier; confirm `.env` matches it |
| pod `AccessDeniedException` | profile lacks DynamoDB read | grant read on `{ns}_{env}_passengers` or switch profile |
| live edits not syncing | edited outside `app-lib/src/app_lib` | edit under the synced path |
| cluster won't create | Docker not running | start Docker Desktop, re-run `make local-setup` |

## Next Steps

- Hand the chart to a customer for a real cluster — see
  [Kubernetes Path to Production](./kubernetes-path-to-production.md).
- Understand the chart, Tiltfile, and ctlptl internals — see the developer doc
  [Kubernetes Infrastructure](../developer-docs/infra/kubernetes.md).
- Add community Kubernetes CLIs (k9s, kubectx) — see
  [Kubernetes Tools](../developer-docs/infra/kubernetes-tools.md).
