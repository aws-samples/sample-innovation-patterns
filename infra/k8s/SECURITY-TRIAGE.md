# infra/k8s/ — SAST triage record

The native **KICS** SAST analyzer scans the Helm chart
(`helm/app-lib/templates/deployment.yaml`) independently and **does not read
`.ash/ash.yaml` suppressions**. It therefore surfaces four `Critical` findings
that must be **dismissed manually, one by one, in the security dashboard**.

This file is the version-controlled record of the dismissal category and
justification for each, so the rationale survives a re-scan and can be re-pasted
verbatim if the findings resurface.

## How to dismiss

For each finding: open it in the security dashboard → set **Status: Dismissed**
→ choose the **Reason** below → paste the matching **Justification** → save.

## Findings

All four originate from the local "split-plane" dev model (compute in a
throwaway k3d cluster, data plane in real AWS via the developer's own
credentials). They are triggered **only** by the local Tilt overlay
(`envs/local-tilt`, `aws.credentials.mode: direct`). The cloud overlay
(`envs/eks`, `mode: none`) renders no host mount and inherits the hardened
container `securityContext`, so none of these can occur in a deployed posture.

| # | Finding | Line | Dismissal reason |
|---|---------|------|------------------|
| 1 | Privilege Escalation Allowed | 26 (initContainer) | **False positive** |
| 2 | Privilege Escalation Allowed | 43 (app container) | **False positive** |
| 3 | Volume Mount With OS Directory Write Permissions | 79 | **Acceptable risk** |
| 4 | Non Kube System Pod With Host Mount | 91 | **Acceptable risk** |

---

### #1 & #2 — Privilege Escalation Allowed (lines 26, 43) — *False positive*

> False positive. The chart **does** set `allowPrivilegeEscalation: false` on
> both the app container and the `copy-aws-credentials` initContainer via the
> shared `securityContext` block in `infra/k8s/helm/app-lib/values.yaml` (which
> also sets `capabilities.drop: [ALL]`, `runAsNonRoot: true`, and
> `seccompProfile: RuntimeDefault`). KICS scans the raw Helm template and flags
> the containers before the templated value (`{{- toYaml .Values.securityContext }}`)
> renders, so it cannot see the control that is actually applied. Verify with:
> `helm template app-lib infra/k8s/helm/app-lib | grep -A1 allowPrivilegeEscalation`
> — every rendered container shows `allowPrivilegeEscalation: false`. No
> privilege-escalation path exists at deploy time.

### #3 & #4 — hostPath mount (lines 79, 91) — *Acceptable risk*

> Acceptable risk — local development artifact, never deployed to a
> managed/cloud cluster. This `hostPath` mount exists only to support the local
> "split-plane" dev model (compute in a throwaway k3d cluster, data plane in
> real AWS) and is present only under the `direct`/`initCopy` credential modes
> used by the local Tilt overlay (`infra/k8s/envs/local-tilt`). Risk is bounded
> by concrete controls: the mount is **`readOnly: true`**, it exposes only the
> **developer's own** `~/.aws` on an ephemeral local k3d node (no shared or
> multi-tenant host, no production data), and it is surfaced into the node by
> `envs/local-tilt/ctlptl-cluster.yaml` for local use only. The cloud overlay
> (`infra/k8s/envs/eks`, `aws.credentials.mode: none`) renders **no** `hostPath`
> and **no** host mount — credentials arrive via a scoped IRSA role — so this
> finding cannot occur in any deployed posture. Rationale is also documented in
> `infra/k8s/envs/eks/values.yaml` and `.ash/ash.yaml` (lines 731–736).

> Alternative category: `Mitigating control` is also defensible for #3/#4
> (mitigations = `readOnly: true` + ephemeral local-only node + `mode: none` in
> cloud). `Acceptable risk` is preferred here because the mount genuinely exists
> (it is not a reporting error) and the argument is "scoped and bounded," not
> "equivalent protection provided elsewhere."

## KICS Kubernetes analyzer — Medium findings (GitLab SAST)

GitLab's KICS **Kubernetes** analyzer scans the raw Helm template the same way
the KICS Critical scanner does (above) — it reads `deployment.yaml` /
`serviceaccount.yaml` / `service.yaml` **before** Helm renders
`{{- toYaml .Values.securityContext }}` and `{{- toYaml .Values.resources }}`,
so it reports controls as missing that the chart actually applies. These do
**not** appear in the ASH report (`.ash/ash.yaml` suppressions do not reach the
native KICS scanner), so they are dismissed here.

Verify every claim below with:
`helm template app-lib infra/k8s/helm/app-lib` — the securityContext block,
`resources` block, and `automountServiceAccountToken: false` all render.

| Finding | Line(s) | Reason | Justification |
|---|---|---|---|
| Seccomp Profile Is Not Configured | 26, 43 | **False positive** | `seccompProfile.type: RuntimeDefault` is set on both containers via the shared `securityContext` in `values.yaml`; renders on every container. |
| NET_RAW Capabilities Not Being Dropped | 26, 43 | **False positive** | `capabilities.drop: [ALL]` is set on both containers via the shared `securityContext`; dropping ALL includes NET_RAW. |
| Container Running As Root | 26, 43 | **False positive** | `runAsNonRoot: true` is set on both containers via the shared `securityContext`. |
| Memory Requests Not Defined | 26 | **False positive** | `resources.requests.memory: 128Mi` renders via `{{- toYaml .Values.resources }}`. |
| Memory Limits Not Defined | 26 | **False positive** | `resources.limits.memory: 512Mi` renders via `{{- toYaml .Values.resources }}`. |
| Service Account Token Automount Not Disabled | 16 | **FIXED** | Chart now sets `automountServiceAccountToken: false` on both the pod spec and the ServiceAccount (`values.yaml`, `deployment.yaml`, `serviceaccount.yaml`). The service calls DynamoDB, never the k8s API. |
| Container Running With Low UID | 26, 43 | **Acceptable risk** | `runAsUser` is intentionally left unset so the image's own non-root UID applies; `runAsNonRoot: true` already guarantees a non-root user. Overlays may pin `runAsUser` (see `values.yaml` note). Bounded: local k3d dev only; cloud uses IRSA + hardened defaults. |
| Using Unrecommended Namespace | svc-account:5, service:3, deployment:4 | **Acceptable risk** | The chart is namespace-agnostic by design — no `metadata.namespace` is hardcoded (that would fork the single-source-of-truth model; see chart CLAUDE.md). The namespace is supplied at install time via `helm install -n <ns>` from the convergence trio, never `default`. |
| S3 Bucket Logging Disabled | tfstate.yml:23 | **Acceptable risk** | KICS-named variant of `CKV_AWS_18`, already dispositioned in `.ash/ash.yaml` (line 351): the Terraform state bucket is internal-only, accessed only by the terraform CLI, and auditable via CloudTrail S3 data events. |

> **Note on the FIXED item:** `automountServiceAccountToken: false` is the one
> Medium that was a genuine gap, not a template-blindness artifact — the chart
> previously never set it. It is now hardened and needs no dashboard dismissal
> once the scan re-runs. All other rows are dismissals.

## Related suppression records

- `.ash/ash.yaml` (lines 731–736) — ASH-side disposition of findings #3/#4.
  ASH does not cover #1/#2 because the hardened `securityContext` already
  resolves them at render time.
- `infra/k8s/envs/eks/values.yaml` — inline `SECURITY` note on why the cloud
  posture is clean.
