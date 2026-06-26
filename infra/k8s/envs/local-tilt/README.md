# local-tilt overlay

Local k3d/Tilt inner-dev-loop configuration for the `app-lib` chart. Consumed
by the repo-root `Tiltfile` and `make local-*` targets — not a customer
artifact.

## Files

| File | Role |
|---|---|
| `values.yaml` | Helm overlay: `AUTH_ENABLED=false`, `aws.credentials.mode=initCopy`, local resources. Documents the T2/T3 preference layer only. |
| `ctlptl-cluster.yaml` | ctlptl `Cluster` + `Registry`. Creates the k3d cluster and maps `${HOME}/.aws` → node `/host-aws` (read-only). |

## Layered config — what lives where

- **T1 (convergence): injected by Tilt, NOT in this overlay.** `APP_NAMESPACE`,
  `APP_ENV`, `AWS_REGION`, `APP_REGION` come from the repo-root `.env` via the
  Tiltfile's `dotenv()` + `helm(set=[...])`. The local pod therefore resolves
  the same DynamoDB table name (`{ns}_{env}_passengers`) the backend tier CFN
  created. Do not hardcode these here — that would fork the source of truth.
- **T2/T3 (preference): in `values.yaml`.** Auth flag, credentials mode, image
  pull policy, replicas, resources. Tune these for local work.

## Split-plane model

The **data plane** (DynamoDB) is stood up by the existing
`/ipa-compose → /ipa-prepare → /ipa-deploy` flow against the backend tier. Only
the **compute plane** (the FastAPI pod) runs locally in k3d. They connect by:

1. **Table-name convergence** — same `APP_NAMESPACE`/`APP_ENV` on both sides.
2. **Host-mounted credentials** — `${HOME}/.aws` → k3d node `/host-aws` (this
   file) → pod `/root/.aws` (the chart's `initCopy` mode).

## ctlptl quirks (do not "fix")

- The `Registry` object uses a **top-level `name:`**, not `metadata.name`.
- The `Cluster` name is a **local literal** (`k3d-ipa-local`), intentionally not
  namespaced — one local cluster is the only use case.
- k3d node volumes go under `k3d.v1alpha5Simple.volumes` (ctlptl passes this
  straight through to k3d's own `SimpleConfig`).
