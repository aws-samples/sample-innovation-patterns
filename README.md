# Innovation Patterns Agent (IPA)

![IPA Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Faws-samples%2Fsample-innovation-patterns%2Fmain%2FVERSION&search=%5E.*%24&label=IPA%20Version&prefix=v)

> **[Read the full documentation](https://aws-samples.github.io/sample-innovation-patterns/)**

Compose and deploy full-stack AWS applications in minutes, not days.

IPA is a library of AI-driven skills that automate AWS infrastructure deployment. You describe what you want — a serverless web app, a queue worker, a CI/CD pipeline — and IPA composes the CloudFormation stacks, generates the Makefiles, and deploys everything to your account.

**The output is designed for your path to production.** IPA generates standard CloudFormation templates, plain GNU Makefiles with inline `aws` CLI calls, and commented `.env` files — no proprietary abstractions, no runtime dependencies on IPA or Claude Code. An AWS engineer can open any generated file, understand it without IPA context, and integrate it into whatever CI/CD pipeline, change management process, or deployment workflow their organization requires. IPA gets you to a working POC fast; the artifacts it produces are the starting point for production, not a dead end.

## What It Deploys

A full-stack composition deploys a complete serverless web application in a single session:

- **Frontend** — React SPA on S3 + CloudFront with OAC
- **Backend** — FastAPI on Lambda + API Gateway v2 with JWT auth
- **Data** — DynamoDB tables (feature-flagged)
- **Auth** — Cognito User Pool with OAuth 2.0 Hosted UI
- **Container Registry** — ECR for Lambda container images
- **Observability** — CloudWatch dashboards and alarms

Additional stacks layer on top: the queue stack adds a background worker, and stacks compose without conflict.

## How It Works

Five skills, run in sequence:

```
/ipa.init → /ipa.security → /ipa.compose → /ipa.prepare → /ipa.deploy
```

| Skill | What It Does |
|-------|-------------|
| `/ipa.init` | Configures the project (namespace, environment, region, AWS account) |
| `/ipa.security` | Provisions IAM roles and a centralized log bucket |
| `/ipa.compose` | Reads a pattern, resolves dependencies, generates Makefiles |
| `/ipa.prepare` | Deploys one-time prerequisite stacks (Cognito, ECR) |
| `/ipa.deploy` | Builds, deploys, and wires everything together |

Every skill is idempotent — safe to re-run at any time.

## Get Started

- **[Installation](https://aws-samples.github.io/sample-innovation-patterns/getting-started/installation)** — Install prerequisites (Python 3.12, Node.js, AWS CLI, Claude Code)
- **[Quickstart](https://aws-samples.github.io/sample-innovation-patterns/getting-started/quickstart)** — Go from zero to a deployed application in one session

## Learn More

- **[Concepts](https://aws-samples.github.io/sample-innovation-patterns/getting-started/concepts)** — What IPA is, how it is organized, and the lifecycle from inception to production handoff
- **[Design Principles](#design-principles)** — The constraints and trade-offs behind IPA's design

## Design Principles

- **Production-compatible output** — every generated artifact (CloudFormation, Makefiles, `.env`) uses standard tooling and is ready to adopt into Jenkins, GitLab CI, CodePipeline, or any other deployment pipeline without modification
- **Self-documenting artifacts** — inline comments, CloudFormation `Description` fields, and Makefile target annotations mean an engineer can read any file and understand the system without consulting IPA documentation
- **No lock-in** — IPA is a composition tool, not a runtime. After deployment, nothing depends on IPA or Claude Code. Delete the skills directory and the system keeps running
- **Convention over configuration** — sensible defaults for region, naming, and structure mean a builder can run skills without reading a setup guide
- **Security by default** — least-privilege IAM, encryption at rest, no public-by-default resources
- **Evolvable POC** — IPA accelerates inception-to-POC; production hardening (HA, multi-AZ, advanced monitoring) is the implementor's next step, shaped by their own requirements
