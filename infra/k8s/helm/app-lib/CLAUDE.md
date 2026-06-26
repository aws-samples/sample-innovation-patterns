# infra/k8s/helm/app-lib/

Helm chart for the `app-lib` FastAPI service. This is **both** the local
k3d/Tilt deploy target **and** the customer handoff artifact — the same chart,
re-pointed by per-environment values overlays in `../../envs/`.

## Design contract

- **Cloud-ready, deployed locally only this round.** Every cloud-specific knob
  (image registry, IRSA annotations, replicas, resources) is a `values` override
  — no chart edits are needed to target a real cluster. We exercise only the
  local overlay; the `eks/` overlay is a non-deployed template.
- **Convergence trio is injected, not hardcoded.** `APP_NAMESPACE`, `APP_ENV`,
  `AWS_REGION`/`APP_REGION` are NOT in `values.yaml`. The Tiltfile reads the
  repo-root `.env` via `dotenv()` and injects them with `helm(set=[...])`. This
  is what makes the local pod resolve the **same** DynamoDB table name
  (`{ns}_{env}_passengers`) that the backend tier CFN created. See
  `infra/cfn/backend/backend.yml` and `app_lib...pynamodb_util.env_table_name`.
- **No secrets in the chart.** Credentials never live in `values.yaml`, the
  image, or rendered manifests. They reach the pod only at runtime via a host
  mount (local) or IRSA (cloud). A grep for credentials across this directory
  must come back empty.

## Files

| File | Purpose |
|---|---|
| `Chart.yaml` | apiVersion v2; `version` = chart, `appVersion` = app-lib release |
| `values.yaml` | production-shaped defaults (auth on, 1 replica, no creds mount default flips to initCopy for local) |
| `templates/deployment.yaml` | single container :8000; env via `range`; `/health` probes; creds volume gated by `aws.credentials.mode` |
| `templates/service.yaml` | ClusterIP, port 8000, `targetPort: http` |
| `templates/serviceaccount.yaml` | gated on `serviceAccount.create`; IRSA-annotatable |
| `templates/_helpers.tpl` | name/fullname/labels/image (63-char DNS truncation) |
| `templates/NOTES.txt` | post-install port-forward + auth/creds status |

## `aws.credentials.mode` toggle

The pod reads a real, AWS-deployed DynamoDB table using the developer's own
credentials (the local "split-plane" model — data plane in AWS, compute plane
in k3d). Three modes:

- **`none`** — mount nothing. The cloud posture: bind a scoped IAM role with
  IRSA on the ServiceAccount. Used by the `eks/` overlay.
- **`direct`** — bind-mount the host creds path read-only straight at
  `mountPath`. Simplest, but ties the long-lived container to a host path and
  assumes the container can read root-owned files.
- **`initCopy`** (default) — an initContainer copies the host creds into an
  `emptyDir` and `chmod`s them, then the app container mounts the copy. Works
  for non-root images and keeps the host path out of the app container.

Both `direct` and `initCopy` must `helm template` cleanly; that is an explicit
acceptance criterion. The host path itself is provisioned into the k3d node by
`../../envs/local-tilt/ctlptl-cluster.yaml` (mounts `${HOME}/.aws` → `/host-aws`).

## Verify

```bash
helm lint infra/k8s/helm/app-lib
helm template app-lib infra/k8s/helm/app-lib
helm template app-lib infra/k8s/helm/app-lib --set aws.credentials.mode=direct
helm template app-lib infra/k8s/helm/app-lib --set aws.credentials.mode=initCopy
```
