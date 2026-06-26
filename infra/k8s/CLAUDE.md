# infra/k8s/

Kubernetes assets for the `app-lib` FastAPI service: a cloud-ready Helm chart
plus per-environment values overlays. This tree is **net-new** and committed as
a living reference asset (the same in-repo model as `infra/cfn/` and
`infra/containers/`) — no IPA skill writes these files into a target project.

## Layout

```text
infra/k8s/
  helm/app-lib/        the chart (Deployment + Service + ServiceAccount)
  envs/
    local-tilt/        LOCAL k3d/Tilt overlay + ctlptl cluster spec (deployed locally)
    eks/               CLOUD overlay TEMPLATE — annotated, NOT deployed this round
  README.md            overview + "Future Work" (deferred cloud automation)
  CLAUDE.md            this file
```

## Operating model — split plane

- **Data plane (AWS):** the DynamoDB table is stood up by the existing
  `/ipa-compose → /ipa-prepare → /ipa-deploy` flow against the backend tier.
- **Compute plane (local):** the FastAPI pod runs in k3d via Tilt.
- **They converge on table name.** `app_lib...pynamodb_util.env_table_name`
  builds `{APP_NAMESPACE}_{APP_ENV}_passengers`; `infra/cfn/backend/backend.yml`
  builds the identical name. The Tiltfile injects the same `APP_NAMESPACE`/
  `APP_ENV`/`AWS_REGION` from the repo-root `.env`, so the local pod reads the
  real deployed table. No CFN-output wiring, no `helm` compose mode.

## Why no `/ipa-compose` integration

A Helm chart has no CloudFormation Parameters/Outputs/`Export: Name` to wire,
so it does not route through `/ipa-compose` (which composes CFN tier stacks).
The k8s offering is a self-contained scaffold + docs deliverable. `/ipa-compose`
is untouched by this feature.

## Verification (CI-safe, no cluster)

```bash
helm lint infra/k8s/helm/app-lib
helm template app-lib infra/k8s/helm/app-lib                                   # default
helm template app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/local-tilt/values.yaml
helm template app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/eks/values.yaml # template only
```

Local end-to-end (`make local-setup && make local-up`) needs Docker + k3d on a
tooled machine — see `docs/guides/kubernetes-local-development.md`.

## Conventions

- **No secrets, ever.** Credentials never appear in the chart, overlays, image,
  or `.env`. They reach the pod at runtime via host-mount (local) or IRSA
  (cloud). A grep of this tree for credentials/account IDs must be clean (the
  only account ID anywhere is the placeholder `123456789012` in `eks/`).
- **EKS guidance has one source:** `envs/eks/CLAUDE.md`. Do not restate it in
  the `/ipa-k8s-help` skill — link to it.
- **Local literals are intentional** (cluster/release/image names are not
  namespaced); documented in `envs/local-tilt/`.
