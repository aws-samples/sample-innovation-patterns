# Kubernetes assets for app-lib

A cloud-ready Helm chart and the local k3d/Tilt inner-dev loop for the `app-lib`
FastAPI service. This round ships **local-only**: a turnkey Tilt loop and a
chart that doubles as the customer handoff artifact. This tree is net-new and
committed as a living reference asset (same in-repo model as `infra/cfn/` and
`infra/containers/`) — no IPA skill writes these files into a target project.

## Contents

| Path | Purpose | Deployed? |
|------|---------|-----------|
| `helm/app-lib/` | The Helm chart (Deployment + Service + ServiceAccount + `_helpers.tpl` + `NOTES.txt`); production-shaped defaults | Locally, via Tilt |
| `helm/app-lib/Chart.yaml` | `apiVersion: v2`; `version` = chart, `appVersion` = `app-lib` release | — |
| `helm/app-lib/values.yaml` | Defaults: auth on, 1 replica, resource limits, `aws.credentials.mode: initCopy` | — |
| `envs/local-tilt/` | Local Helm overlay + `ctlptl-cluster.yaml` (k3d cluster + registry) | Yes — `make local-up` |
| `envs/eks/` | Annotated cloud overlay **template** + single-source EKS guidance (`CLAUDE.md`) | No — copy-and-customize |

## Quick start (local)

```bash
make doctor        # check tools (docker, kubectl, helm, k3d, tilt, ctlptl, aws)
make local-setup   # create the k3d cluster + registry
make local-up      # build + deploy via Tilt; port-forward :8000
curl localhost:8000/health   # -> {"status":"ok"}
make local-destroy # tear down
```

Stand up the data plane first with `/ipa-compose → /ipa-prepare → /ipa-deploy`
(backend tier, `EnablePassengersTable=true`). Full walkthrough:
`docs/guides/kubernetes-local-development.md`.

## Split-plane data flow

The data plane and compute plane are deployed separately and converge at runtime:

- **Data plane (AWS):** the DynamoDB table is stood up by the existing
  `/ipa-compose → /ipa-prepare → /ipa-deploy` flow against the backend tier.
- **Compute plane (local):** the `app-lib` FastAPI pod runs in k3d via Tilt.
- **Convergence on table name:** `PynamodbUtil.env_table_name` builds
  `{APP_NAMESPACE}_{APP_ENV}_passengers`; `infra/cfn/backend/backend.yml` builds
  the identical name. The `Tiltfile` injects the same env values from repo-root
  `.env`, so the local pod reads the real deployed table. No CFN-output wiring.
- **Credential path:** host `~/.aws` → k3d node `/host-aws` (mapped by
  `ctlptl-cluster.yaml`, read-only) → pod `/root/.aws` (via the chart's
  `aws.credentials.mode`). The pod uses the developer's own IAM identity.

## Credential modes (`aws.credentials.mode`)

| Mode | Behavior | Used by |
|------|----------|---------|
| `none` | mount nothing; bind a scoped IAM role via IRSA on the ServiceAccount | cloud (`envs/eks/`) |
| `direct` | bind-mount host creds read-only at `mountPath` | local (simple) |
| `initCopy` (default) | initContainer copies host creds into an `emptyDir` and `chmod`s them; the app then mounts the copy (non-root-safe) | local |

## Environment Variables

These are application env vars the chart renders into the pod (from `.Values.env`
plus the injected convergence trio). The chart itself reads no env vars.

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `APP_NAMESPACE` | Yes | Tiltfile from `.env` (local); overlay `env` (cloud) | First segment of the DynamoDB table name |
| `APP_ENV` | Yes | Tiltfile from `.env` (local); overlay `env` (cloud) | Second segment of the table name |
| `AWS_REGION` | Yes | Tiltfile from `.env` (local); overlay `env` (cloud) | AWS region for the SDK |
| `APP_REGION` | Yes | Tiltfile from `.env` (local); overlay `env` (cloud) | Region alias set alongside `AWS_REGION` so both agree |
| `AUTH_ENABLED` | No | chart default `"true"`; `local-tilt` overlay sets `"false"` | JWT auth toggle |
| `AWS_CONFIG_FILE` / `AWS_SHARED_CREDENTIALS_FILE` | No | rendered by the chart when `mode != none` | Point the SDK at `{mountPath}/config` and `{mountPath}/credentials` |

## Known Quirks

- **ctlptl `Registry` uses a top-level `name:`**, not `metadata.name` (a ctlptl
  convention). k3d node volumes go under `k3d.v1alpha5Simple.volumes` — a
  passthrough to k3d's own `SimpleConfig`.
- **Convergence trio is injected, not stored.** Editing a values overlay to add
  `APP_NAMESPACE`/`APP_ENV`/`AWS_REGION` defeats the single-source-of-truth
  design — the Tiltfile owns those, sourced from `.env`.
- **Cloud overlays must set `aws.credentials.mode: none`.** Any other mode
  renders a `hostPath` volume that does not exist on a managed cloud node.
- **Local literals are intentional.** The cluster/release/image names are not
  namespaced — running more than one local cluster is not a use case (KISS).
- **`envs/eks/` is rendered, never applied.** `helm template -f` validates it;
  IPA applies nothing cloud-side this round.

## Integration Points

- **`/ipa-compose` is untouched.** A Helm chart has no CFN Parameters/Outputs/
  `Export: Name` to wire, so the k8s offering is a self-contained scaffold + docs
  deliverable rather than a compose target.
- **Container image:** the chart deploys `infra/containers/rest-k8s/` (plain
  uvicorn on `:8000`), built and live-updated by the repo-root `Tiltfile`.
- **Lifecycle:** the root `Makefile` `doctor`/`local-setup`/`local-up`/
  `local-destroy`/`local-reset` targets drive the loop.
- **Helper skill:** `/ipa-k8s-help` guides setup/troubleshooting (local) and the
  manual EKS path, referencing `envs/eks/CLAUDE.md` as the single source.

## Future Work (not implemented)

The following cloud-cluster automation is **deliberately deferred** this round.
None of it is built; this section records the intended path so a future round
(or a customer) can pick it up:

1. **Cluster provisioning (CFN/Terraform).** Infrastructure-as-code to stand up
   an EKS (or AKS) cluster, its node groups, and the OIDC provider needed for
   IRSA. IPA provisions no cluster today.
2. **ECR wiring.** A repository for the `rest-k8s` image and a push step. Today
   the local loop uses a Tilt-built local image; cloud image management is the
   customer's.
3. **IRSA role creation.** The scoped IAM role + trust policy that the chart's
   ServiceAccount annotation (`eks.amazonaws.com/role-arn`) binds to. The chart
   is IRSA-*annotatable*; the role itself is not created by IPA.
4. **CodePipeline `helm upgrade --install` stage.** A pipeline stage that
   applies the chart to the cluster on each change. No remote `helm install`
   target and no pipeline stage exist today.
5. **Local IRSA.** OIDC provider + Pod Identity Webhook for scoped per-pod
   credentials locally, replacing the host-mount. Deferred; the host-mount is
   the POC path.
6. **Ingress templates.** Cluster exposure (ALB Ingress, Gateway API) is left to
   the customer's overlay and is not templated by the chart.

Until these land, IPA accelerates the **review** of a cloud deploy (cloud-ready
chart + annotated overlay + guidance in `envs/eks/CLAUDE.md`), not the **apply**.

## Related

- See [CLAUDE.md](./CLAUDE.md) for the grab-and-go conventions and gotchas.
- `helm/app-lib/CLAUDE.md` — chart internals and the credential-mode toggle.
- `envs/eks/CLAUDE.md` — single-source EKS guidance and pre-deploy checklist.
- `docs/docs/developer-docs/infra/kubernetes.md` — full chart/Tilt/ctlptl/Makefile internals.
