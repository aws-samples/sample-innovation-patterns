---
title: Path to Production
sidebar_position: 7
---

# Path to Production

## Overview

This guide covers the steps to take an IPA composition from a development deployment to a production-ready state. By the end, the reader has a hardened configuration, resolved security findings, and a complete set of handoff artifacts that a customer team can deploy independently.

## When to Use This Guide

Use this guide when:

- An IPA engagement is nearing completion and the composition must be handed off to the customer team
- A deployed development composition needs to be transitioned to a staging or production environment
- The security disposition register must be reviewed and findings resolved before production
- Preparing Makefile-as-contract deliverables for the customer team to operate independently

Do not use this guide for initial development deployment — see "Composing a Solution" and `/ipa-deploy` instead.

## Before You Start

Before you start, confirm the following:

- A stable, tested composition is deployed in a development environment via `/ipa-init`, `/ipa-security`, `/ipa-compose`, and `/ipa-deploy`
- `scripts/SECURITY-DISPOSITION.md` exists and has been reviewed at least once
- CI/CD pipeline is configured (see "CI/CD with CodePipeline") or a plan for the customer pipeline is in place
- Customer deployment requirements have been gathered: naming conventions, network constraints, compliance requirements, and tagging standards
- Access to the production AWS account is available, or the customer has provided account details

## Before / Target State

| Before | After |
|--------|-------|
| A working development deployment operated by the builder. Development defaults for security, capacity, and networking. Security findings documented but not all addressed. No production environment configured. | A hardened composition with production configuration applied. All security findings resolved or explicitly accepted with stakeholder sign-off. Customer team has Makefiles, CloudFormation templates, security register, and environment configuration to deploy and operate independently. |

## Steps

### 1. Review the security disposition register

To understand the current security posture, open and review `scripts/SECURITY-DISPOSITION.md`. The register contains two sections:

- **Pattern Deferrals** — security findings inherited from the composed patterns, accepted for POC scope
- **Custom Dispositions** — project-specific findings documented during development

Categorize each finding into one of three dispositions for production:

| Category | Action | Example |
|----------|--------|---------|
| **Resolved** | The finding has been addressed in the production configuration | CF-1: Custom domain and ACM certificate configured |
| **Accepted** | The customer accepts the risk with documented rationale | SQS-1: Standard queue is sufficient for the workload |
| **Requires Decision** | The customer team must evaluate and decide | CF-2: WAF configuration depends on customer compliance requirements |

Update the Custom Dispositions section of `SECURITY-DISPOSITION.md` with the production status of each finding.

### 2. Harden stack configuration

Review the CloudFormation templates and update parameters for production use.

**Parameterized settings** — update via pattern Config and re-compose, or via Makefile `--parameter-overrides`:

| Stack | Parameter | Dev Default | Production Recommendation |
|-------|-----------|-------------|--------------------------|
| Cognito | `DeletionProtection` | `INACTIVE` | `ACTIVE` |
| Cognito | `MinPasswordLength` | `8` | `12` or higher |
| Backend | `AlarmSnsTopicArn` | (empty) | Production SNS topic ARN |
| Queue | `AlarmSnsTopicArn` | (empty) | Production SNS topic ARN |
| Backend | `MemorySize` | `512` | Size based on workload profiling |
| Queue | `MemorySize` | `512` | Size based on workload profiling |

**Hardcoded settings** — require CloudFormation template edits in `infra/cfn/`:

| Stack | Setting | Dev Value | Production Change |
|-------|---------|-----------|-------------------|
| Cognito | Token validity | 8h access, 24h refresh | Reduce to 60min access, 7-day refresh |
| Frontend | `PriceClass` | `PriceClass_100` (US/Canada/Europe) | `PriceClass_All` for global reach |
| Frontend | Custom domain | CloudFront default `*.cloudfront.net` | Add ACM certificate and `Aliases` |
| ECR | `ImageTagMutability` | `MUTABLE` | `IMMUTABLE` to prevent tag overwrites |

After making changes, re-run `/ipa-compose` to regenerate Makefiles with the updated parameter overrides.

:::warning
Token validity, PriceClass, custom domains, and ECR mutability are hardcoded in the CloudFormation templates. Changing these requires editing the YAML files in `infra/cfn/` directly — they are not configurable via Makefile parameter overrides alone.
:::

### 3. Configure production environment

To create a production environment configuration, copy `.env.example` and set the production values:

```bash
cp .env.example .env
```

Update the core variables for the production account:

```
APP_NAMESPACE=myapp
APP_ENV=prod
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
AWS_PROFILE=prod-profile
```

The `APP_NAMESPACE` and `APP_ENV` values determine all stack names. For example, `APP_NAMESPACE=myapp` and `APP_ENV=prod` produce stack names like `myapp-prod-backend` and `myapp-prod-frontend`.

### 4. Update callback URLs and domains

After the production environment is configured, update authentication and distribution settings:

a. **Cognito callback URL** — The default `CallbackURL` is `http://localhost:8080/authentication/callback`. For production with a custom domain, set it to `https://yourdomain.com/authentication/callback`. If using the CloudFront default domain, the post-deploy step updates this automatically.

b. **Cognito domain prefix** — The prefix must be globally unique across all AWS accounts. The compose engine generates it as `{APP_NAMESPACE}-{APP_ENV}-{APP_ACCOUNT_HASH}`, where `APP_ACCOUNT_HASH` is derived from the AWS account ID. Verify that the generated prefix is not already in use.

c. **Custom domain** — If the customer requires a custom domain (for example, `app.customer.com`):
   - Create an ACM certificate in `us-east-1` (required for CloudFront) and validate it via DNS
   - Add the certificate ARN and domain alias to the frontend CloudFormation template at `infra/cfn/frontend/frontend.yml`
   - Configure DNS (CNAME or Route 53 alias) to point to the CloudFront distribution

### 5. Recalculate IAM permissions

To provision security infrastructure for the production environment, run:

```
/ipa-security
```

The skill reads `APP_NAMESPACE` and `APP_ENV` from `.env` and creates:

- **Builder execution role**: `{APP_NAMESPACE}-{APP_ENV}-builder` — for deployments
- **CodeBuild execution role**: `{APP_NAMESPACE}-{APP_ENV}-codebuild` — for CI/CD pipelines
- **Centralized log bucket**: `{APP_NAMESPACE}-{APP_ENV}-logs-{AWS_ACCOUNT_ID}-{AWS_REGION}` — with versioning enabled, 90-day lifecycle, and SSL-only access policy

The skill writes `APP_BUILDER_ROLE_ARN` and `APP_CODEBUILD_ROLE_ARN` to `.env`. If the customer provides pre-provisioned IAM roles instead, select the "Existing Role ARNs" path when prompted.

### 6. Prepare handoff artifacts

Inventory and organize the deliverables for the customer team. A complete handoff includes:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Makefiles | `scripts/*.mk` | Deployment contract — all targets the customer runs |
| CloudFormation templates | `infra/cfn/**/*.yml` | Infrastructure definitions |
| Environment template | `.env.example` | Configuration template for new environments |
| Security register | `scripts/SECURITY-DISPOSITION.md` | Documented security findings and dispositions |
| Pattern architecture | `.claude/skills/ipa-compose/patterns/*/ARCHITECTURE.md` | System architecture and deployment diagrams |

Verify that `.env.example` includes all variables the customer needs with placeholder values. Remove any builder-specific credentials from the example file.

:::note
The customer team does not need the `.claude/` directory or IPA skills to deploy. The generated Makefiles in `scripts/` are self-contained — the customer runs `make -f scripts/deploy.mk deploy` directly.
:::

### 7. Validate with a dry run

Before handing off to the customer, validate the production configuration. To preview deployment commands without executing them, run a dry run against each Makefile:

```bash
make -n -f scripts/prepare.mk prepare
make -n -f scripts/deploy.mk deploy
make -n -f scripts/post-deploy.mk post-deploy
```

Each command prints the `aws cloudformation deploy` invocations with resolved stack names and parameter overrides. Verify that:

- Stack names use the production namespace and environment (for example, `myapp-prod-backend`)
- Parameter overrides include the hardened values from Step 2
- IAM role ARNs reference the production security stack

If a staging environment is available, deploy the full composition to staging first to confirm the configuration works end-to-end before proceeding to production.

### 8. Document customer adaptations

Create a list of changes the customer team must make to adapt the composition for their organizational standards. Common adaptations include:

- **Naming conventions** — stack names, resource tags, and log prefixes that must match the customer taxonomy
- **Network configuration** — VPC placement, security groups, or private subnets if the customer does not use the default VPC
- **Compliance requirements** — encryption key management (KMS), log retention periods, or audit trail configuration beyond the 90-day default
- **Tagging standards** — additional resource tags required by the customer cost allocation or governance policies
- **CI/CD integration** — how the customer existing pipeline connects to the Makefile targets

Document these adaptations alongside the handoff artifacts so the customer team has a clear path from receiving the deliverables to operating in production.

## Verification

To confirm that the production readiness process is complete:

1. Verify that all security findings in `SECURITY-DISPOSITION.md` are categorized as Resolved or Accepted — no findings remain as Requires Decision:

   ```bash
   grep -c "Requires Decision" scripts/SECURITY-DISPOSITION.md
   ```

   Expected output: `0`

2. Verify that deletion protection is active on the Cognito stack:

   ```bash
   aws cloudformation describe-stacks \
     --stack-name myapp-prod-cognito \
     --query 'Stacks[0].Parameters[?ParameterKey==`DeletionProtection`].ParameterValue' \
     --output text
   ```

   Expected output: `ACTIVE`

3. Verify that the production Makefiles resolve with the correct stack names:

   ```bash
   make -n -f scripts/deploy.mk deploy 2>&1 | grep "stack-name"
   ```

   All stack names should use the production namespace and environment (for example, `myapp-prod-backend`).

4. Verify that the customer team can execute the Makefiles independently by confirming that `scripts/deploy.mk` does not reference any builder-specific paths or credentials.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Stack deployment fails with `AccessDenied` in the production account | The production IAM role does not have sufficient permissions, or the role trust policy does not allow the deploying principal | Verify the role ARN in `.env` matches the production security stack outputs and confirm the trust policy allows the deploying user or service |
| Cognito domain prefix conflict (`DomainAlreadyExistsException`) | The domain prefix must be globally unique across all AWS accounts | Change `APP_NAMESPACE` or `APP_ENV` to produce a different prefix, or use a custom domain instead of the Cognito hosted domain |
| CloudFront distribution creation takes 15-30 minutes | This is expected CloudFront behavior for new distributions | Wait for the distribution to reach `Deployed` status — do not cancel or retry the deployment |
| Customer deployment fails due to VPC or network restrictions | The CloudFormation templates use default VPC and public subnets, which may not exist in the customer account | Add VPC, subnet, and security group parameters to the relevant templates, or work with the customer to configure their network |

## Next Steps

- **Compose the solution** — see "Composing a Solution" for how Makefiles and wiring were generated
- **Set up CI/CD** — see "CI/CD with CodePipeline" for automated build and deploy pipelines
- **Stack reference** — see the Stacks section for per-stack parameters, outputs, and architecture diagrams
- **Tear down infrastructure** — run `/ipa-destroy` to delete deployed stacks
