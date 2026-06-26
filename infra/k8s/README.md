# Kubernetes assets for app-lib

A cloud-ready Helm chart and the local k3d/Tilt inner-dev loop for the `app-lib`
FastAPI service. This round ships **local-only**: a turnkey Tilt loop and a
chart that doubles as the customer handoff artifact. Cloud-cluster automation is
**future work** (see below).

## What is here

| Path | What | Deployed? |
|---|---|---|
| `helm/app-lib/` | The Helm chart (Deployment + Service + ServiceAccount) | Locally, via Tilt |
| `envs/local-tilt/` | Local overlay + ctlptl k3d cluster/registry spec | Yes — `make local-up` |
| `envs/eks/` | Annotated cloud overlay **template** | No — copy-and-customize example |

## Quick start (local)

```bash
make doctor        # check tools (docker, kubectl, helm, k3d, tilt, ctlptl, aws)
make local-setup   # create the k3d cluster + registry
make local-up      # build + deploy via Tilt; port-forward :8000
curl localhost:8000/health   # -> {"status":"ok"}
make local-destroy # tear down
```

The pod reads a **real deployed** DynamoDB table using your host `~/.aws`
credentials (split-plane model). Stand up the data plane first with
`/ipa-compose → /ipa-prepare → /ipa-deploy` (backend tier,
`EnablePassengersTable=true`). Full walkthrough:
`docs/guides/kubernetes-local-development.md`.

## Customer handoff

The chart is the handoff artifact. A customer deploys to their own cluster with
`helm` alone — no IPA, no Claude Code — by writing their own values overlay
(`envs/eks/` is a worked example). See
`docs/guides/kubernetes-path-to-production.md`.

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
