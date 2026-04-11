---
title: Installation
sidebar_position: 3
---

# Installation

Detailed prerequisite setup for local development. If you already have the required tools, skip to the [Quickstart](quickstart.md).

## Python 3.12

The backend requires Python >=3.12,<3.13.

**Check your version:**
```bash
python3 --version
```

**Install with pyenv (recommended):**
```bash
# Install pyenv (macOS)
brew install pyenv

# Install Python 3.12
pyenv install 3.12
pyenv local 3.12    # Set for this project directory
```

**Install with Homebrew (macOS):**
```bash
brew install python@3.12
```

## uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. The backend uses it for dependency management.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

:::tip pip works too
If you prefer pip, all backend deps can be installed with `pip install -e ".[all]"` from the `app-lib/` directory. The `uv sync --all-extras` command is faster but functionally equivalent.
:::

## Node.js 22+

The frontend requires Node.js 22 or later.

**Check your version:**
```bash
node --version
```

**Install with nvm (recommended):**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# Install Node.js 22
nvm install 22
nvm use 22
```

**Install with Homebrew (macOS):**
```bash
brew install node@22
```

## AWS CLI v2 (Optional)

Required for backend features that access DynamoDB, Bedrock, and SQS. Not needed for frontend-only development.

**Install:**
```bash
# macOS
brew install awscli

# Verify
aws --version
```

**Configure a profile:**
```bash
aws configure --profile your-profile-name
```

Then set `AWS_PROFILE=your-profile-name` in the project root `.env` file.

## Project Dependencies

After installing the tools above, install project dependencies:

```bash
# Backend (from project root)
cd app-lib && uv sync --all-extras && cd ..

# Frontend (from project root)
cd web-client && npm install && cd ..
```

You're ready to go. Run `make dev` from the project root to start developing. See the [Quickstart](quickstart.md) for details.
