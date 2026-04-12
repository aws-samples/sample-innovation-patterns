---
title: Notebook Development
sidebar_position: 4
---

# Notebook Development

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide sets up a Jupyter notebook environment for prototyping and testing against deployed IPA infrastructure. By the end, the reader can execute notebooks that interact with DynamoDB tables, invoke Bedrock models, send SQS messages, and authenticate through Cognito from a local Jupyter session.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: prototyping AI/ML workflows with Bedrock before backend integration; exploring DynamoDB data interactively; demonstrating backend capabilities to stakeholders; debugging queue processing by manually publishing SQS messages.

## Before You Start

> **Guidance:** Prerequisites: /ipa.deploy completed, Python 3.12 and Jupyter installed, .env configured, AWS CLI configured, app-lib/ dependencies installed.

## Before / Target State

> **Guidance:** Before: Deployed AWS infrastructure. No interactive environment. Testing requires full API endpoints. After: Jupyter notebooks running locally with AWS credentials, able to import app-lib modules, query DynamoDB, invoke Bedrock, and send SQS messages interactively.

## Steps

> **Guidance:** 5 steps. Source files: app-lib/ (importable Python modules), .env, any existing notebooks in the repo.

### 1. Install notebook dependencies

> **Guidance:** Install Jupyter and create a kernel linked to the project Python environment.

### 2. Configure the notebook kernel

> **Guidance:** Set up the kernel with the correct Python path and environment variables.

### 3. Load environment variables

> **Guidance:** Show how to load .env into the notebook session (e.g., python-dotenv).

### 4. Import app-lib modules

> **Guidance:** Demonstrate importing project modules and using them interactively.

### 5. Test connectivity

> **Guidance:** Run a simple AWS operation (DynamoDB scan, Bedrock invoke) to confirm the setup works.

## Verification

> **Guidance:** Run a cell that lists DynamoDB tables. Import an app-lib module and call a function. Confirm Bedrock model invocation returns a response.

## Next Steps

> **Guidance:** Link to local-development guide, app-lib/ developer docs, relevant stack or Bedrock documentation.
