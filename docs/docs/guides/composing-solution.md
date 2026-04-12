---
title: Composing a Solution
sidebar_position: 2
---

# Composing a Solution

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide walks through selecting and assembling IPA stacks into a deployable composition. By the end, the reader has a composed project with generated Makefiles, security disposition register, and environment configuration ready for /ipa.prepare and /ipa.deploy. Explain how /ipa.compose works as a stack selector, how stacks wire together automatically, and what artifacts are generated.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: starting a new IPA project after /ipa.init and /ipa.security; adding stacks to an existing composition; re-composing after modifying stack configuration; understanding what /ipa.compose generates before running it.

## Before You Start

> **Guidance:** Prerequisites: /ipa.init completed, /ipa.security completed, AWS CLI configured, familiarity with available stacks (frontend, backend, queue as deploy stacks; cognito, ecr as prepare stacks).

## Before / Target State

> **Guidance:** Before: An initialized IPA project with .env configured and security roles provisioned. No Makefiles, no stack wiring, no deployment artifacts. After: scripts/ directory populated with prepare.mk, build.mk, deploy.mk, post-deploy.mk, env.mk, and test.mk. SECURITY-DISPOSITION.md generated. Stack parameter wiring resolved across all selected stacks.

## Steps

> **Guidance:** 6 steps. Source files: .claude/skills/ipa.compose/SKILL.md (compose skill behavior), scripts/MAKEFILE\_TEMPLATES.md (Makefile generation templates), infra/cfn/ subdirectories (stack parameters and outputs for wiring).

### 1. Review available stacks

> **Guidance:** List deploy stacks (frontend, backend, queue) and prepare stacks (cognito, ecr) with what each deploys.

### 2. Run /ipa.compose

> **Guidance:** Invoke the compose skill. Show the interactive stack selection. Explain that prepare dependencies (cognito, ecr) are included automatically when needed.

### 3. Review generated Makefiles

> **Guidance:** Walk through scripts/prepare.mk, build.mk, deploy.mk, post-deploy.mk, env.mk, test.mk. Explain what each controls.

### 4. Review stack wiring

> **Guidance:** Show how outputs from one stack become parameters for another (e.g., Cognito UserPoolClientId to Backend AuthAudience). Reference the generated Makefile parameter-overrides.

### 5. Review the security disposition register

> **Guidance:** Explain SECURITY-DISPOSITION.md: what it documents, how to read it, why it matters for the customer handoff.

### 6. Add additional stacks

> **Guidance:** Optional. Show how to re-run /ipa.compose to add a stack (e.g., queue) to an existing composition. Explain that existing configuration is preserved.

## Verification

> **Guidance:** Verify scripts/ directory contains the expected Makefiles. Verify SECURITY-DISPOSITION.md exists and lists the composed stacks. Run make -f scripts/deploy.mk --dry-run to confirm Makefile targets parse correctly. Check .env for any new variables added by compose.

## Troubleshooting

> **Guidance:** Conditional section. Potential entries: missing .env variables causing compose to fail; re-compose overwriting manual Makefile edits; stack dependency resolution failures.

## Next Steps

> **Guidance:** Link to /ipa.prepare documentation, deployment guide or /ipa.deploy, Stacks section for per-stack parameters, /ipa.destroy documentation.
