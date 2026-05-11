---
title: Installation
sidebar_position: 2
---

# Installation

This page lists the prerequisites for working with Innovation Patterns (IPA). Install each tool before proceeding to the [Quickstart](quickstart.md).

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 (`>=3.12,<3.13`) | Backend application library (`app-lib/`) |
| Node.js | 18+ (LTS recommended) | Frontend web client (`web-client/`) and documentation site (`docs/`) |
| uv | Latest | Python project and dependency management |
| AWS CLI | v2 | AWS service interaction and CloudFormation deployments |
| Docker | Latest | Container image builds for Lambda deployment |
| GNU Make | Any | Execution of generated Makefiles (`scripts/*.mk`) |
| Claude Code | Latest | AI agent that runs IPA skills (`/ipa-*`) |

## Python 3.12

IPA requires Python 3.12 exactly (`>=3.12,<3.13`). Verify your installation:

```bash
python3 --version
```

If you do not have Python 3.12, install it via your system package manager or [python.org](https://www.python.org/downloads/).

**macOS (Homebrew):**

```bash
brew install python@3.12
```

**Linux (apt):**

```bash
sudo apt update && sudo apt install python3.12 python3.12-venv
```

## Node.js

Node.js 18 or later is required for the web client and the documentation site. Verify:

```bash
node --version
```

Install via [nodejs.org](https://nodejs.org/) or a version manager such as `nvm`:

```bash
nvm install --lts
```

## uv

uv is the Python package and project manager used by `app-lib/`. Verify:

```bash
uv --version
```

Install via the standalone installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:

```bash
brew install uv
```

## AWS CLI v2

The AWS CLI is required for all CloudFormation operations. Verify:

```bash
aws --version
```

Install following the [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

After installation, configure credentials for your target AWS account. IPA supports the default credential chain (environment variables, SSO, instance profiles) or a named profile. The `/ipa-init` skill configures which profile to use.

## Docker

Docker is required to build container images for Lambda deployment. Verify:

```bash
docker --version
```

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows) or Docker Engine (Linux).

Ensure the Docker daemon is running before invoking `/ipa-deploy`.

## GNU Make

GNU Make executes the generated Makefiles that drive build, deploy, and teardown operations. Verify:

```bash
make --version
```

**macOS:** Pre-installed with Xcode Command Line Tools (`xcode-select --install`).

**Linux:** Pre-installed on most distributions. If missing:

```bash
sudo apt install make
```

## Claude Code

Claude Code is the AI agent CLI that executes IPA skills. All IPA workflows (`/ipa-init`, `/ipa-compose`, `/ipa-deploy`, etc.) run as Claude Code skills.

Install following the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/overview).

## Verify All Prerequisites

Run the following commands to confirm all tools are installed:

```bash
python3 --version
node --version
uv --version
aws --version
docker --version
make --version
claude --version
```

All commands should return version information without errors. Proceed to the [Quickstart](quickstart.md) to configure and deploy your first IPA project.
