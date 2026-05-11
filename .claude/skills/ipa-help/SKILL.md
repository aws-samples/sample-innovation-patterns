---
name: ipa-help
description: "Report IPA project state and suggest the next lifecycle skill to run."
model: opus
---

# /ipa-help — IPA Project State Inspector

Reports the current state of an IPA project and suggests the next lifecycle skill.
Does not run any skill automatically.

**Lifecycle**: `/ipa-init` → `/ipa-compose` → `/ipa-prepare` → `/ipa-deploy`

---

## What This Skill Does

1. Reads `.env` (if present) to determine initialization and security state
2. Checks `scripts/prepare.mk` and `scripts/deploy.mk` existence to determine composition state
3. Queries AWS CloudFormation for stack deployment status
4. Reports a one-line state summary with a suggested next skill

## What This Skill Does NOT Do

- Does not run any skill automatically — it only suggests
- Does not list individual stacks or dump `.env` contents
- Does not troubleshoot failures or diagnose errors
- Does not modify any files or deploy any infrastructure

---

## State Detection

> **AWS credential resolution**: All `aws` CLI commands must be prefixed with `source .env 2>/dev/null;` to load credentials into the environment. Do NOT pass `--profile` or `--region` flags explicitly.

### Step 1: Read Filesystem State

1. Check if `.env` exists at the project root.
2. If `.env` exists, read it and check for:
   - `APP_NAMESPACE` (set by `/ipa-init`)
   - `APP_ENV` (set by `/ipa-init`)
   - `APP_BUILDER_ROLE_ARN` (set by `/ipa-security` via `/ipa-compose`)
3. Check if `scripts/deploy.mk` exists.
4. Check if `scripts/prepare.mk` exists.

### Step 2: Query AWS Stack Status (if credentials available)

If `.env` contains `APP_NAMESPACE` and `APP_ENV`, attempt to query stack status:

1. **Security stack**: `{APP_NAMESPACE}-{APP_ENV}-security`
2. **Prepare stacks**: Parse `scripts/prepare.mk` (if exists) for stack names, query each.
3. **Deploy stacks**: Parse `scripts/deploy.mk` (if exists) for stack names, query each.

For each stack:
```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name {stack-name} --query 'Stacks[0].StackStatus' --output text
```

If AWS calls fail (no credentials, network issues): degrade gracefully. Report filesystem state and note "AWS status unavailable."

---

## Decision Matrix

| State | Detection | Suggestion |
|-------|-----------|-----------|
| Not initialized | `.env` missing or `APP_NAMESPACE` absent | Run `/ipa-init` |
| Initialized, not composed | `.env` present, no `scripts/deploy.mk` | Run `/ipa-compose <stacks>` |
| Composed, security missing | `scripts/deploy.mk` present, `APP_BUILDER_ROLE_ARN` absent or security stack not `*_COMPLETE` | Run `/ipa-compose` (triggers security phase) |
| Composed, not prepared | Prepare stacks defined in `prepare.mk` but not deployed | Run `/ipa-prepare` |
| Prepared, not deployed | Prepare stacks `*_COMPLETE`, deploy stacks missing | Run `/ipa-deploy` |
| Fully deployed | All stacks `*_COMPLETE` | Deployment complete. Use `/ipa-destroy` to tear down. |

---

## Output Format

One-line state summary, followed by a single "Next:" line naming the suggested skill
with a minimal invocation example. No stack listings, no `.env` dump.

**Example outputs:**

```
State: Initialized, not composed.
Next: Run `/ipa-compose frontend backend` to compose your infrastructure.
```

```
State: Composed, prepare stacks not deployed.
Next: Run `/ipa-prepare` to deploy one-time prerequisites.
```

```
State: Fully deployed (all stacks active).
Next: Deployment complete. Use `/ipa-destroy` to tear down when done.
```

```
State: Initialized, security not configured.
Next: Run `/ipa-compose` — security configuration runs on first compose.
```
