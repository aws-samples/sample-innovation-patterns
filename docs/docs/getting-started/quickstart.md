---
title: Quickstart
sidebar_position: 3
---

# Quickstart

This page walks through configuring, composing, and deploying a full-stack serverless application using IPA skills. By the end, you will have a React frontend served via CloudFront, a FastAPI backend on Lambda with SQS for background processing, DynamoDB tables, Cognito authentication, and an ECR container registry — all deployed to your AWS account.

## Before You Start

- All [prerequisites](installation.md) are installed (Python 3.12, Node.js, uv, AWS CLI, Docker, GNU Make, Claude Code)
- You have AWS credentials configured for the target account
- Docker Desktop is running
- You are in the Innovation Patterns repository root directory

## Workflow Overview

IPA deploys infrastructure through four skills:

```
/ipa-init → /ipa-compose → /ipa-prepare → /ipa-deploy
```

| Skill | What It Does |
|-------|-------------|
| `/ipa-init` | Configures the project — writes `.env` with namespace, environment, region, and AWS account |
| `/ipa-compose` | Reads stack skills and generates Makefiles for build, deploy, and teardown. On first run, prompts for security configuration (IAM roles). |
| `/ipa-prepare` | Deploys one-time prerequisite stacks (log bucket, Cognito, ECR) |
| `/ipa-deploy` | Builds container images, deploys all stacks, and runs post-deploy wiring |

:::tip
Not sure what to run next? Use `/ipa-help` — it inspects your project state and recommends the next skill.
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
3. The skill exits and points you at `/ipa-compose`

:::note
If you skip this step and jump straight to `/ipa-compose`, it will auto-run `/ipa-init` for you when `.env` is missing.
:::

## Step 2: Compose a Pattern

Run:

```
/ipa-compose I would like a web app with a REST API and SQS for background processing
```

You can describe what you want in natural language — the skill resolves your description to available stack skills (`frontend`, `backend`, `queue`).

On first compose, if `APP_BUILDER_ROLE_ARN` is absent from `.env`, the skill prompts for security configuration — choose the recommended **Innovation Builder Stack** path for the fastest setup, or provide an existing role ARN.

The compose skill assembles the selected stacks into a full-stack serverless web application:

- **Cognito** — User Pool with OAuth 2.0 Hosted UI (prepare stack, auto-included)
- **ECR** — Container image repository (prepare stack, auto-included)
- **Queue** — SQS + DLQ + worker Lambda + EventSourceMapping + DynamoDB jobs table (deploy stack)
- **Backend** — Lambda + API Gateway v2 + DynamoDB passengers table + SQS integration (deploy stack)
- **Frontend** — S3 + CloudFront + OAC (deploy stack)

### What Happens

The skill reads stack skills from `.claude/skills/ipa-stack-*/`, resolves dependencies and parameter wiring (including auto-enabling `EnableSqsIntegration=true` on the backend when queue is present), and generates seven artifacts:

| File | Purpose |
|------|---------|
| `scripts/prepare.mk` | Deploys prerequisite stacks (Cognito, ECR) |
| `scripts/deploy.mk` | Deploys application stacks (queue → backend → frontend) |
| `scripts/build.mk` | Builds the shared container image and frontend assets |
| `scripts/post-deploy.mk` | Configures frontend, uploads to S3, invalidates CloudFront, wires Cognito callbacks and backend CORS |
| `scripts/env.mk` | Syncs deployed stack outputs to `.env` for local development |
| `scripts/test.mk` | Validates CloudFormation templates |
| `scripts/SECURITY-DISPOSITION.md` | Security disposition register |

## Step 3: Prepare Prerequisites

Run:

```
/ipa-prepare
```

The skill deploys one-time prerequisite stacks (Cognito and ECR) that must exist before the application can be built and deployed.

### What Happens

- Cognito User Pool is provisioned with OAuth 2.0 Hosted UI and a globally-unique domain prefix
- ECR repository is created for container images
- OIDC configuration and ECR URI are written to `.env` for downstream use

## Step 4: Deploy

Run:

```
/ipa-deploy
```

The skill validates all prerequisites (including that Docker is running), displays a deployment plan, and asks for confirmation. If prepare stacks have not been deployed, it tells you to run `/ipa-prepare` first.

After confirmation, it executes the full deployment pipeline:

1. **Build** — The shared `rest-lambda` container image is built and pushed to ECR (used by both backend and queue worker); frontend assets are compiled with Vite
2. **Deploy** — Queue, backend, and frontend CloudFormation stacks are created in dependency order
3. **Post-deploy** — Environment variables are synced, sample data is loaded, frontend `config.js` is generated, assets are uploaded to S3, CloudFront cache is invalidated, Cognito callback URLs and backend CORS are updated with the CloudFront domain

### What Happens

After a successful deployment, the completion report displays:

- Stack statuses (all `CREATE_COMPLETE`)
- Application URL (CloudFront) — open this in a browser
- API URL (API Gateway)
- All post-deploy steps completed (env sync, data load, frontend config, S3 upload, CDN invalidation, auth wiring, CORS wiring)

## After Deployment

### Access the Application

Open the Application URL from the deployment report in a browser. The Cognito Hosted UI handles user sign-up and sign-in.

:::tip
Ask Claude Code to create a Cognito user for you:

```
Can you create a cognito user <your-username> : <your-password> that does not have to be changed
```

Claude will use `admin-create-user` followed by `admin-set-user-password --permanent` to create a confirmed user that can sign in immediately — no email verification or password change required.
:::

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

```
/ipa-destroy
```

Or run the Makefile directly:

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

- Run `/ipa-compose codepipeline` then `/ipa-prepare` to set up CI/CD with CodePipeline
- Explore the [Stacks](/stacks) section for per-stack reference documentation
- Read the [Developer Docs](/developer-docs) for codebase conventions and contribution guidelines
