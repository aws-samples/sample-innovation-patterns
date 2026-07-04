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

GitLab's KICS **Kubernetes** analyzer **does** render the Helm chart before
scanning (it runs `helm template` internally), so — unlike the KICS Critical
scanner noted above — it sees the values injected through
`{{- toYaml .Values.securityContext }}` and `{{- toYaml .Values.resources }}`.
We confirmed this: after the `securityContext` was hardened, the Seccomp /
NET_RAW / "Running As Root" Mediums **disappeared** on the next scan, and the
surviving findings' line numbers tracked edits to the template. So the Mediums
below were **real gaps**, not template-blindness — most are now **fixed in the
chart**, and only two classes remain as documented dispositions.

These findings do **not** appear in the ASH report (`.ash/ash.yaml` suppressions
do not reach the native KICS scanner), so the two remaining dispositions must be
dismissed in the dashboard.

Verify every fix below with:
`helm template app-lib infra/k8s/helm/app-lib` — the `securityContext` (incl.
`runAsUser: 10001`), the app **and** initContainer `resources` blocks, and
`automountServiceAccountToken: false` all render.

| Finding | Line(s) | Reason | Justification |
|---|---|---|---|
| Seccomp Profile Is Not Configured | app + init container | **FIXED** | `seccompProfile.type: RuntimeDefault` in the shared `securityContext` (`values.yaml`) renders on both containers. Resolved on re-scan. |
| NET_RAW Capabilities Not Being Dropped | app + init container | **FIXED** | `capabilities.drop: [ALL]` in the shared `securityContext` renders on both containers (dropping ALL includes NET_RAW). Resolved on re-scan. |
| Container Running As Root | app + init container | **FIXED** | `runAsNonRoot: true` in the shared `securityContext`. Resolved on re-scan. |
| Service Account Token Automount Not Disabled | pod spec | **FIXED** | `automountServiceAccountToken: false` on both the pod spec and the ServiceAccount (`values.yaml`, `deployment.yaml`, `serviceaccount.yaml`). The service calls DynamoDB, never the k8s API. |
| Memory Requests Not Defined | initContainer | **FIXED** | The initCopy initContainer previously declared no `resources`. It now renders `.Values.initResources` (requests 16Mi / limits 32Mi). The app container already had `.Values.resources`. |
| Memory Limits Not Defined | initContainer | **FIXED** | Same as above — `initResources.limits.memory: 32Mi` renders on the initContainer. |
| Container Running With Low UID | app + init container | **FIXED** | `runAsUser: 10001` added to the shared `securityContext`, matching the rest-k8s image's `appuser` (Dockerfile `--uid 10001`). This is the UID both containers already ran as, so it changes nothing at runtime — it just makes the high (>=10000), non-root UID explicit so the scanner can confirm it. |
| Using Unrecommended Namespace | serviceaccount, service, deployment | **Acceptable risk** | The chart is namespace-agnostic by design — no `metadata.namespace` is hardcoded (that would fork the single-source-of-truth model; see chart CLAUDE.md). The namespace is supplied at install time via `helm install -n <ns>` from the convergence trio, never `default`. **Dismiss in dashboard.** |
| S3 Bucket Logging Disabled | tfstate.yml:23 | **Acceptable risk** | KICS-named variant of `CKV_AWS_18`, already dispositioned in `.ash/ash.yaml` (line 351): the Terraform state bucket is internal-only, accessed only by the terraform CLI, and auditable via CloudTrail S3 data events. **Dismiss in dashboard.** |

> **Most of these were genuine gaps and are now fixed in the chart** — they need
> no dashboard action once the scan re-runs and clears them. Only the two
> **Acceptable risk** rows (Unrecommended Namespace ×3, tfstate S3 logging)
> remain as manual dismissals, because both reflect deliberate design choices
> rather than missing controls.
>
> **Correction:** an earlier draft of this table labeled the Seccomp / NET_RAW /
> Root / Memory findings "false positive (template blindness)." That was wrong —
> KICS does render the chart. They were real, and are now fixed rather than
> dismissed.

## Related suppression records

- `.ash/ash.yaml` (lines 731–736) — ASH-side disposition of findings #3/#4.
  ASH does not cover #1/#2 because the hardened `securityContext` already
  resolves them at render time.
- `infra/k8s/envs/eks/values.yaml` — inline `SECURITY` note on why the cloud
  posture is clean.
