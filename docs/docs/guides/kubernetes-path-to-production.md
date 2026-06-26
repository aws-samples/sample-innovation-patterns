---
title: Kubernetes Path to Production
sidebar_position: 12
---

# Kubernetes Path to Production

## Overview

This guide explains how a customer takes the `app-lib` Helm chart to a real
Kubernetes cluster. By the end, you understand the chart as a handoff artifact,
how to write a cloud values overlay, and exactly which parts of the cloud path
IPA accelerates this round (the review) and which remain the customer's work
(the apply).

## When to Use This Guide

Use this guide when an engagement is moving the local Kubernetes loop toward a
real cluster (EKS or otherwise), or when preparing the chart for customer
handoff. For the local inner-dev loop, see
[Kubernetes Local Development](./kubernetes-local-development.md).

## Before You Start

- A working local loop is the best starting point — see
  [Kubernetes Local Development](./kubernetes-local-development.md).
- For a real deploy, the customer needs: a Kubernetes cluster, a container
  registry (e.g. ECR) with the image pushed, and — for AWS access — an IRSA IAM
  role with a scoped DynamoDB policy. IPA provisions none of these this round.
- `helm` and `kubectl` configured against the target cluster.

## Before / Target State

**Before:** The chart is deployed locally only, against a k3d cluster, using a
host credential mount.

**Target:** The customer understands how to deploy the same chart to their own
cluster with their own values overlay and `helm` alone — no IPA, no Claude Code.

## Steps

1. **Take the chart as the handoff artifact.** The chart at
   `infra/k8s/helm/app-lib/` is cloud-ready: image, environment, replicas,
   resources, and the ServiceAccount's IRSA annotation are all values-overridable.
   No chart edit is needed to target a cluster.

2. **Copy the worked cloud overlay.** `infra/k8s/envs/eks/values.yaml` is an
   annotated, **non-deployed** template. Copy it to your own environment
   directory, e.g. `infra/k8s/envs/<your-cluster>/values.yaml`.

3. **Customize the overlay.** Fill in every placeholder: the ECR image URI, the
   IRSA role ARN (replace the placeholder account ID `123456789012`), the
   namespace/region in `env`, and resource sizing. Read
   `infra/k8s/envs/eks/CLAUDE.md` — the single source of EKS guidance and the
   pre-deploy review checklist.

4. **Render to inspect** (this does not deploy anything):

   ```bash
   helm template app-lib infra/k8s/helm/app-lib -f infra/k8s/envs/<your-cluster>/values.yaml
   ```

5. **Deploy on your own terms** (the customer runs this):

   ```bash
   helm upgrade --install app-lib infra/k8s/helm/app-lib \
     -f infra/k8s/envs/<your-cluster>/values.yaml
   ```

## Verification

```bash
kubectl get pods -l app.kubernetes.io/name=app-lib
kubectl port-forward svc/app-lib 8000:8000
curl -s localhost:8000/health      # -> {"status":"ok"}
```

The chart deploying with `helm` alone — no IPA tooling — is the proof of
cloud-readiness.

## Future Work (not implemented)

IPA does **not** automate the cloud deploy this round. The following are
deliberately deferred and recorded here and in `infra/k8s/README.md`:

- **Cluster provisioning** — CFN/Terraform to stand up EKS (or AKS), node
  groups, and the OIDC provider for IRSA.
- **ECR wiring** — a repository for the image and an automated push.
- **IRSA role creation** — the scoped IAM role and OIDC trust the chart's
  ServiceAccount annotation binds to.
- **CodePipeline `helm upgrade --install` stage** — a pipeline stage that
  applies the chart on each change.
- **Local IRSA** — scoped per-pod credentials locally, replacing the host-mount.
- **Ingress templates** — cluster exposure (ALB Ingress, Gateway API).

The framing for this round: **IPA accelerates the *review*, not the *apply*.**
You get a cloud-ready chart, an annotated overlay, and a review checklist so the
path to a cluster is short and well-understood — but standing up the cluster and
applying the chart remain the customer's work.

## Next Steps

- Walk the overlay and validate cloud pre-conditions interactively — run
  `/ipa-k8s-help` and choose the EKS scope.
- Review the chart/Tilt/ctlptl internals — see
  [Kubernetes Infrastructure](../developer-docs/infra/kubernetes.md).
