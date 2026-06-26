# infra/k8s/

Cloud-ready Helm chart + per-environment values overlays for the `app-lib` FastAPI service. Deployed **locally only** this round (k3d/Tilt); the chart is also the customer cloud handoff artifact.

- This offering does NOT route through `/ipa-compose` (a Helm chart has no CFN Parameters/Outputs to wire). Do not add a `helm`/`k8s` compose mode.
- The convergence trio (`APP_NAMESPACE`/`APP_ENV`/`AWS_REGION`/`APP_REGION`) is NOT in any values file — the `Tiltfile` injects it from repo-root `.env` via `helm(set=...)`. Hardcoding it into an overlay forks the source of truth.
- `aws.credentials.mode` gates the creds mount: `none` (cloud/IRSA) · `direct` (hostPath) · `initCopy` (default; initContainer→emptyDir). Cloud overlays MUST use `none` — a hostPath mount fails on a managed node.
- `envs/eks/` is a TEMPLATE, NOT deployed; the only account ID in this tree is the placeholder `123456789012`. Never commit a real account ID or any credential here.
- `envs/local-tilt/ctlptl-cluster.yaml`: the `Registry` uses a top-level `name:` (NOT `metadata.name`); k3d node volumes go under `k3d.v1alpha5Simple.volumes`.
- EKS guidance has one source — `envs/eks/CLAUDE.md`. Reference it; don't restate its steps.

See README.md for the contents map, split-plane data flow, env vars, integration points, and the deferred cloud "Future Work".
