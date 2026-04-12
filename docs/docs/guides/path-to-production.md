---
title: Path to Production
sidebar_position: 7
---

# Path to Production

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide covers the steps to take an IPA composition from a development deployment to a production-ready state. By the end, the reader understands the handoff artifacts, configuration changes, and hardening steps required before the customer team takes ownership.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: engagement nearing completion and composition must be handed off; transitioning from dev to staging or production; preparing Makefile-as-contract deliverables for the customer; reviewing the security disposition register before production.

## Before You Start

> **Guidance:** Prerequisites: stable tested composition deployed in dev, /ipa.compose /ipa.prepare /ipa.deploy all completed, CI/CD pipeline configured or a plan for the customer pipeline, SECURITY-DISPOSITION.md reviewed, customer deployment requirements gathered (naming, network, compliance, tagging).

## Before / Target State

> **Guidance:** Before: A working development deployment operated by the builder. Development defaults. Security findings documented but not all addressed. No production environment. After: Documented, hardened composition with production configuration. Customer team has Makefile targets, CloudFormation templates, security register, and environment configuration to deploy independently.

## Steps

> **Guidance:** 8 steps. Source files: scripts/SECURITY-DISPOSITION.md (security findings register), all .mk files under scripts/ (Makefile targets forming the execution contract), .claude/skills/ipa.security/SKILL.md (security skill for IAM recalculation), all .yml files under infra/cfn/ subdirectories (CloudFormation templates with production-relevant parameters like DeletionProtection).

### 1. Review the security disposition register

> **Guidance:** Walk through SECURITY-DISPOSITION.md. Categorize findings as addressed, accepted, or requiring customer decision.

### 2. Harden stack configuration

> **Guidance:** Enable deletion protection, review capacity settings, configure alarms, tighten token validity.

### 3. Configure production environment

> **Guidance:** Create production .env with appropriate namespace, environment, region, and account values.

### 4. Update callback URLs and domains

> **Guidance:** Configure production OAuth callback URLs, CloudFront domain, custom domain setup if applicable.

### 5. Recalculate IAM permissions

> **Guidance:** Re-run /ipa.security for the production environment.

### 6. Prepare handoff artifacts

> **Guidance:** Inventory and organize all deliverables for the customer team: Makefile targets, CloudFormation templates, .env.example, security register, architecture diagrams.

### 7. Validate with a dry run

> **Guidance:** Deploy to a staging environment to confirm production configuration works end-to-end.

### 8. Document customer adaptations

> **Guidance:** List changes the customer team must make for their organizational standards (naming conventions, network configurations, compliance requirements).

## Verification

> **Guidance:** All SECURITY-DISPOSITION.md findings addressed or explicitly accepted. Production deployment succeeds end-to-end via Makefile targets. Deletion protection active on persistent resources (Cognito, DynamoDB). Customer team can execute make deploy independently.

## Troubleshooting

> **Guidance:** Conditional section. Potential entries: stack deployment fails in production account (IAM role differences); Cognito domain prefix conflict (must be globally unique); CloudFront distribution takes extended time to deploy (expected); customer VPC or network restrictions block deployment.

## Next Steps

> **Guidance:** Link to composing-solution guide, codepipeline guide, Stacks reference, /ipa.destroy documentation, IPA Concept document (builder-to-customer handoff model).
