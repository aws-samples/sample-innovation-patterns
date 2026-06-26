# infra/k8s/envs/eks/ — EKS guidance (single source)

**This file is the authoritative source of EKS guidance for the k8s offering.**
The `/ipa-k8s-help` skill's EKS scope *references* this file rather than
restating the steps — keep the guidance here so the two cannot drift.

## Posture this round: manual and reviewed, applies nothing

IPA stands up no cluster, wires no ECR, creates no IRSA role, and applies
nothing to a cloud cluster this round. What IPA ships is:

- a **cloud-ready chart** (`infra/k8s/helm/app-lib/`) — image/env/serviceAccount
  values-overridable, ServiceAccount IRSA-annotatable, no chart edit needed; and
- this **annotated `eks/` overlay template** to copy and customize.

IPA accelerates the **review** of a cloud deploy, not the **apply**.

## Pre-conditions to validate before a cloud deploy (guidance-only)

When guiding a builder through the EKS path, validate — never create — these,
and degrade gracefully (report "cannot verify") when a cloud resource is
unreachable:

1. **Credentials** — `aws sts get-caller-identity` succeeds for an identity that
   can administer the target cluster.
2. **Target context** — `kubectl config current-context` points at the intended
   EKS cluster (NOT the local k3d cluster).
3. **ECR repository** — the image repository in the overlay exists and the image
   tag has been pushed (`aws ecr describe-images`).
4. **IRSA role present** — the IAM role named in
   `serviceAccount.annotations."eks.amazonaws.com/role-arn"` exists, has a trust
   policy for the cluster's OIDC provider, and grants the DynamoDB permissions
   the app needs (scoped to `{namespace}_{env}_passengers`, not `*`).
5. **Convergence** — the overlay's `APP_NAMESPACE`/`APP_ENV`/`AWS_REGION` resolve
   to the table the customer intends the pod to read.

## The IRSA model (cloud) vs. host-mount (local)

| | Local (k3d/Tilt) | Cloud (EKS) |
|---|---|---|
| Credentials | developer's `~/.aws` host-mounted into the pod | per-pod role via IRSA |
| Scope | the developer's full IAM identity (broad) | scoped IAM role (least privilege) |
| Chart knob | `aws.credentials.mode: initCopy\|direct` | `aws.credentials.mode: none` + SA annotation |

The local host-mount is a deliberate POC trade-off (the credentials are the
developer's own, mounted at runtime, never embedded). IRSA is the scoped,
production-appropriate path — and it is why the chart's ServiceAccount is
IRSA-annotatable from day one.

## Review checklist (apply nothing)

- [ ] `helm template ... -f eks/values.yaml` renders with the real ECR image and
      the IRSA annotation, no errors.
- [ ] No account ID other than the placeholder `123456789012` appears until the
      customer fills in their own.
- [ ] `aws.credentials.mode` is `none` (no host mount on a managed node).
- [ ] Ingress/exposure decided out-of-chart (ALB Ingress, Gateway API, or a
      LoadBalancer Service in the customer overlay).

## Future work (not implemented)

Cluster provisioning (CFN/Terraform for EKS), ECR wiring, IRSA role creation,
and a CodePipeline stage that runs `helm upgrade --install` are all deferred.
See `infra/k8s/README.md` for the recorded future-work path.
