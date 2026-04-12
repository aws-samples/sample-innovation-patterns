---
title: Extending with Skills
sidebar_position: 6
---

# Extending with Skills

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide walks through creating a custom IPA stack skill using /ipa.author.stack. By the end, the reader has authored a new stack skill with a CloudFormation template, SKILL.md, and SECURITY.md that integrates with /ipa.compose and the existing Makefile generation pipeline.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: engagement requires an AWS service not in the built-in stacks (e.g., RDS, ElastiCache, Step Functions); adding a custom tier; wrapping an existing CloudFormation template as a composable stack skill; extending the stack library for reuse across engagements.

## Before You Start

> **Guidance:** Prerequisites: familiarity with CloudFormation authoring, understanding of the IPA skill structure (.claude/skills/ipa.stack.NAME/ directory layout), an initialized project with at least one successful /ipa.compose, the CloudFormation template or design for the new stack. Reference files: .claude/skills/ipa.author.stack/SKILL.md, .claude/skills/ipa.stack.backend/ (tier example), .claude/skills/ipa.stack.ecr/ (simple example).

## Before / Target State

> **Guidance:** Before: A CloudFormation template or design for infrastructure not part of built-in stacks. Cannot be composed with /ipa.compose. After: A complete stack skill at .claude/skills/ipa.stack.NAME/ with SKILL.md, SECURITY.md, and a CloudFormation template at infra/cfn/NAME/. The new stack appears as a selectable option in /ipa.compose.

## Steps

> **Guidance:** 7 steps. Source files: .claude/skills/ipa.author.stack/SKILL.md (authoring skill), existing stack skills for structural reference.

### 1. Design the stack interface

> **Guidance:** Define parameters, outputs, lifecycle (prepare or deploy), and wiring to other stacks.

### 2. Run /ipa.author.stack

> **Guidance:** Invoke the authoring skill. Explain what it scaffolds.

### 3. Write the CloudFormation template

> **Guidance:** Create the template following IPA conventions: namespace/environment parameters, export naming.

### 4. Complete the SKILL.md

> **Guidance:** Document the full skill metadata: parameters, outputs, wiring contract, lifecycle classification.

### 5. Write the SECURITY.md

> **Guidance:** Document security posture, IAM permissions, and any cdk\_nag or cfn\_nag suppressions with rationale.

### 6. Test composition

> **Guidance:** Run /ipa.compose with the new stack selected. Verify Makefiles are generated correctly.

### 7. Deploy and verify

> **Guidance:** Deploy the new stack and confirm resources are created as expected.

## Verification

> **Guidance:** /ipa.compose shows the new stack as a selectable option. Generated Makefiles include targets for the new stack. aws cloudformation describe-stacks confirms deployment. Outputs are accessible to downstream stacks via CloudFormation exports.

## Next Steps

> **Guidance:** Link to composing-solution guide, developer-docs/skills/stack-skills/ reference, developer-docs/skills/author-skills/ reference, /ipa.security documentation for recalculating permissions.
