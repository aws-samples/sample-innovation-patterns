# eks overlay — copy-and-customize worked example (NOT a deployed environment)

**This is a template, not a live environment.** IPA does not deploy it. There
is no EKS cluster, no ECR wiring, no IRSA role, and no pipeline that applies
this overlay this round. The directory is named `eks/` for clarity, but the
directory name alone does not mean "deployed" — this README and the leading
comment in `values.yaml` are the authority: **nothing here is applied by IPA.**

## What this is for

`values.yaml` is a fully-annotated example of what a **cloud** values overlay
for the `app-lib` chart looks like — every override a real cluster needs
(registry image, IRSA ServiceAccount annotation, replicas, resources, the
convergence env trio), with an inline comment at each point.

## How to use it

1. **Copy** this overlay to your own environment directory, e.g.
   `infra/k8s/envs/<your-cluster>/values.yaml`.
2. **Customize** every placeholder: the ECR image URI, the IRSA role ARN
   (replace the placeholder account ID `123456789012`), the namespace/region in
   `env`, and the resource sizing.
3. **Provision the prerequisites yourself** — the EKS cluster, the ECR
   repository, and the IRSA IAM role + OIDC trust. The chart consumes these; it
   does not create them.
4. **Render to inspect** (no deploy):

   ```bash
   helm template app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/eks/values.yaml
   ```

5. **Deploy on your own terms** (you run this, not IPA):

   ```bash
   helm upgrade --install app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/<your-cluster>/values.yaml
   ```

## Guidance

`CLAUDE.md` in this directory is the **single source** of EKS guidance — the
pre-conditions to validate, the IRSA model, and the review checklist. The
`/ipa-k8s-help` skill references that file rather than restating it. Read it
before adapting this overlay.

## What IPA accelerates here

The **review**, not the **apply**. IPA gives you a cloud-ready chart and an
annotated overlay so the path to a cluster is short and well-understood — but
standing up the cluster and applying the chart remain the customer's work. See
`docs/guides/kubernetes-path-to-production.md`.
