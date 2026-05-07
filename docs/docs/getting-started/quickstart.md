---
title: Quickstart
sidebar_position: 3
---

# Quickstart

This page walks through configuring, composing, and deploying a full-stack serverless application using IPA skills. By the end, you will have a React frontend served via CloudFront, a FastAPI backend on Lambda, DynamoDB tables, Cognito authentication, and an ECR container registry — all deployed to your AWS account.

## Before You Start

- All [prerequisites](installation.md) are installed (Python 3.12, Node.js, uv, AWS CLI, Docker, GNU Make, Claude Code)
- You have AWS credentials configured for the target account
- Docker Desktop is running
- You are in the Innovation Patterns repository root directory

## Workflow Overview

IPA deploys infrastructure through three user-facing skills:

```
/ipa-init → /ipa-compose → /ipa-deploy
```

| Skill | What It Does |
|-------|-------------|
| `/ipa-init` | Configures the project — writes `.env` with namespace, environment, region, and AWS account. Auto-chains to `/ipa-security` to provision IAM roles and a centralized log bucket on first run. |
| `/ipa-compose` | Reads a pattern definition and generates Makefiles for build, deploy, and teardown |
| `/ipa-deploy` | Builds container images, deploys all stacks, and runs post-deploy wiring. Auto-triggers `/ipa-prepare` when prerequisite stacks (Cognito, ECR) are not yet deployed. |

:::note
`/ipa-security` and `/ipa-prepare` still exist as standalone skills and can be invoked directly if you want to review or update security infrastructure or re-run prepare. In the normal flow, you don't need to — `/ipa-init` and `/ipa-deploy` chain to them automatically.
:::

## Step 1: Initialize the Project

Open Claude Code in the repository root and run:

```
/ipa-init
```

The skill prompts for four configuration values. Accept the defaults for the fastest setup:

| Setting | Default | Description |
|---------|---------|-------------|
| AWS Profile | Skip | Uses the default AWS credential chain |
| AWS Region | `us-east-1` | Deployment region |
| Namespace | `app` | Prefix for all CloudFormation stack names |
| Environment | `dev` | Environment label (dev, stage, prod) |

The skill auto-detects your AWS account ID and writes all values to `.env`.

### What Happens

1. `.env` is created with project configuration variables
2. `.env.example` is generated for team onboarding
3. If `APP_BUILDER_ROLE_ARN` is absent from `.env`, `/ipa-security` runs automatically:
   - Prompts for an IAM configuration path (accept the default **managed policy** with `PowerUserAccess` for the fastest setup)
   - Deploys a CloudFormation stack (`{namespace}-{env}-security`) with IAM roles and an S3 log bucket
   - Writes `APP_BUILDER_ROLE_ARN` and `APP_CODEBUILD_ROLE_ARN` to `.env`

If security infrastructure is already configured, `/ipa-init` exits and points you at `/ipa-compose`.

## Step 2: Compose a Pattern

Run:

```
/ipa-compose
```

The compose skill assembles the selected stacks into a full-stack serverless web application:

- **Cognito** — User Pool with OAuth 2.0 Hosted UI (prepare stack)
- **ECR** — Container image repository (prepare stack)
- **Backend** — Lambda + API Gateway v2 + DynamoDB + CloudWatch (deploy stack)
- **Frontend** — S3 + CloudFront + OAC (deploy stack)

### What Happens

The skill reads the pattern definition, resolves stack dependencies and parameter wiring, and generates six Makefiles:

| File | Purpose |
|------|---------|
| `scripts/prepare.mk` | Deploys prerequisite stacks (Cognito, ECR) |
| `scripts/deploy.mk` | Deploys application stacks (backend, frontend) |
| `scripts/build.mk` | Builds container images and frontend assets |
| `scripts/post-deploy.mk` | Configures frontend, uploads to S3, invalidates CloudFront, wires Cognito callbacks |
| `scripts/env.mk` | Syncs deployed stack outputs to `.env` for local development |
| `scripts/test.mk` | Validates CloudFormation templates |

A security disposition register is also generated at `scripts/SECURITY-DISPOSITION.md`.

## Step 3: Deploy

Run:

```
/ipa-deploy
```

The skill validates all prerequisites, displays a deployment plan, and asks for confirmation. After confirmation, it executes the full deployment pipeline:

1. **Prepare** — If prerequisite stacks (Cognito, ECR) are not yet deployed, `/ipa-prepare` runs automatically
2. **Build** — Container images are built and pushed to ECR; frontend assets are compiled
3. **Deploy** — Backend and frontend CloudFormation stacks are created
4. **Post-deploy** — Frontend `config.js` is generated, assets are uploaded to S3, CloudFront cache is invalidated, and Cognito callback URLs are updated

### What Happens

After a successful deployment, the completion report displays:

- Stack statuses (all `CREATE_COMPLETE`)
- Stack outputs (Lambda ARN, API URL, CloudFront URL)
- Application URL — open this in a browser to access the deployed application

## After Deployment

### Access the Application

Open the Application URL from the deployment report in a browser. The Cognito Hosted UI handles user sign-up and sign-in.

### Local Development

To run the backend and frontend locally:

**Backend** (FastAPI on port 8000):

```bash
cd app-lib && make run
```

**Frontend** (Vite dev server on port 5173, proxies `/api` to backend):

```bash
cd web-client && npm install && npm run dev
```

### Teardown

To remove deployed stacks when no longer needed:

```bash
make -f scripts/deploy.mk teardown
```

:::warning
Prepare stacks (Cognito, ECR) are not auto-deleted by teardown. To remove them:
```bash
make -f scripts/prepare.mk teardown-prepare
```
:::

### Re-Deploy

All IPA skills are idempotent. Re-run `/ipa-deploy` at any time to update the deployment. CloudFormation handles the state — unchanged stacks are skipped, updated stacks are deployed in place.

## Next Steps

- Re-run `/ipa-compose` and add the queue stack to layer an SQS worker onto the existing deployment
- Run `/ipa-codepipeline` to set up CI/CD with CodePipeline
- Explore the [Stacks](/stacks) section for per-stack reference documentation
- Read the [Developer Docs](/developer-docs) for codebase conventions and contribution guidelines
