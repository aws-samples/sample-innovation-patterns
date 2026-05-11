---
title: Notebook Development
sidebar_position: 4
---

# Notebook Development

## Overview

This guide sets up a Jupyter notebook environment for prototyping and testing against deployed IPA infrastructure. By the end, the reader can execute notebooks that import `app-lib` modules, query DynamoDB tables, invoke Bedrock models, and send SQS messages from a local Jupyter session.

## When to Use This Guide

Use this guide when:

- Prototyping AI/ML workflows with Bedrock before integrating them into the FastAPI backend
- Exploring DynamoDB data interactively using the project's PynamoDB models and data services
- Demonstrating backend capabilities to stakeholders in a visual, step-by-step format
- Debugging queue processing by manually constructing and publishing SQS messages

Do not use this guide for running the full FastAPI backend or React frontend locally. See [Local Development](local-development.md) for that workflow.

## Before You Start

Before you start, confirm the following:

- Infrastructure is deployed via `/ipa-deploy` (DynamoDB tables, SQS queues, and Bedrock model access must exist in the target AWS account)
- Python 3.12 is installed
- `.env` file exists in the project root with `APP_NAMESPACE`, `APP_ENV`, and `AWS_REGION` set (see `.env.example`)
- AWS CLI is configured with credentials for the target account (via `AWS_PROFILE` or the default credential chain)
- `app-lib/` dependencies are installed (Step 1 covers this if not yet done)

## Before / Target State

| Before | After |
|--------|-------|
| Deployed AWS infrastructure (DynamoDB, SQS, Bedrock access). No interactive environment for exploring these services. | Jupyter notebooks running locally with a dedicated kernel, able to import `app-lib` modules, query DynamoDB, invoke Bedrock, and send SQS messages interactively. |
| Testing backend logic requires running the full FastAPI server or deploying Lambda functions. | Individual modules can be tested and prototyped cell-by-cell in a notebook. |

## Steps

### 1. Install notebook dependencies

To install `app-lib` with all dependencies including the Jupyter kernel package, run from the project root:

```bash
pip install -e "app-lib[all]"
```

This installs the core dependencies (`boto3`, `python-dotenv`, `loguru`), the REST extras (`fastapi`, `pynamodb`), and development tools including `ipykernel` for Jupyter integration.

:::note
If using `uv` as the package manager, run `uv pip install -e "app-lib[all]"` instead.
:::

### 2. Register the Jupyter kernel

To make the project Python environment available as a Jupyter kernel, run:

```bash
python -m ipykernel install --user --name app-lib --display-name "Python (app-lib)"
```

The command outputs the kernel installation path, confirming the kernel is registered:

```
Installed kernelspec app-lib in /Users/<username>/Library/Jupyter/kernels/app-lib
```

When creating or opening a notebook, select the **Python (app-lib)** kernel to ensure `app-lib` modules are importable.

### 3. Load environment variables

At the top of each notebook, load the project `.env` file and enable autoreload for interactive development. Add a cell with the following content:

```python
%load_ext autoreload
%autoreload 2

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
```

The `find_dotenv()` function searches upward from the notebook's directory to locate the project root `.env` file. The `autoreload` extension reloads imported modules automatically when their source files change, which is useful when editing `app-lib` code alongside notebook work.

The cell output displays `True` when the `.env` file is loaded successfully.

### 4. Import and use app-lib modules

With the environment loaded, `app-lib` modules are available for import. The following examples demonstrate common interactive workflows.

**a. Query DynamoDB with the passenger data service:**

```python
from app_lib.features.passengers.service.passenger_data_service import TitanicPassengerDataService

service = TitanicPassengerDataService()
passengers = service.list(limit=5)

for p in passengers:
    print(f"{p.name} (Class {p.pclass}), Survived: {p.survived}")
```

**b. Invoke a Bedrock model:**

```python
import boto3
import os

client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))

response = client.converse(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[
        {"role": "user", "content": [{"text": "Summarize the Titanic dataset in one sentence."}]}
    ],
    inferenceConfig={"maxTokens": 256, "temperature": 0.7},
)

print(response["output"]["message"]["content"][0]["text"])
```

**c. Send an SQS message:**

```python
from app_lib.features.jobs.service.sqs_service import SqsService
import os

sqs = SqsService(queue_url=os.environ.get("SQS_QUEUE_URL"))

message_id = sqs.send_message({
    "job_type": "passenger_analysis",
    "passenger_id": "1",
    "prompt": "Analyze this passenger record"
})

print(f"Message sent: {message_id}")
```

:::warning
Sending SQS messages triggers the worker Lambda function in the deployed environment. Use caution when submitting messages to production queues.
:::

### 5. Test connectivity

To confirm the notebook environment can reach all deployed services, run each check in a separate cell.

**DynamoDB — list tables:**

```python
import boto3
import os

dynamodb = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
tables = dynamodb.list_tables()["TableNames"]

namespace = os.environ.get("APP_NAMESPACE", "")
env = os.environ.get("APP_ENV", "")
project_tables = [t for t in tables if t.startswith(f"{namespace}_{env}_")]

print(f"Project tables ({namespace}_{env}_*):")
for t in project_tables:
    print(f"  {t}")
```

**Bedrock — list available models:**

```python
bedrock = boto3.client("bedrock", region_name=os.environ.get("AWS_REGION", "us-east-1"))
models = bedrock.list_foundation_models(byProvider="Anthropic")["modelSummaries"]

for m in models:
    print(f"  {m['modelId']}")
```

Each cell should produce output without errors. If a cell raises an `AccessDeniedException` or `ResourceNotFoundException`, see the Troubleshooting section.

## Verification

To verify the complete setup, open the existing example notebook:

```
app-lib/notebooks/examples/hello-app-lib.ipynb
```

Select the **Python (app-lib)** kernel and run all cells. The notebook loads the `.env` file and calls `app_lib.main.hello()`. Expected output:

```
hello world!
```

Then confirm AWS connectivity by running the DynamoDB table listing from Step 5. The output should include tables prefixed with the project's `APP_NAMESPACE` and `APP_ENV` values (for example, `myproject_dev_passengers`).

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: No module named 'app_lib'` | Notebook is using a different kernel than the one linked to the `app-lib` environment. | Select **Python (app-lib)** from the kernel picker. If the kernel is not listed, re-run Step 2. |
| `ResourceNotFoundException` on DynamoDB operations | `APP_NAMESPACE` or `APP_ENV` is not set, causing table name resolution to fail. | Confirm `.env` is loaded (`load_dotenv` returns `True`) and that `APP_NAMESPACE` and `APP_ENV` match the deployed stack. |
| `AccessDeniedException` on Bedrock or DynamoDB calls | AWS credentials are not configured or lack required permissions. | Verify `aws sts get-caller-identity` returns the expected account. Confirm the IAM role has Bedrock and DynamoDB access. |
| `SQS_QUEUE_URL not set` error when using SqsService | The queue stack is not deployed or the `.env` file does not include `SQS_QUEUE_URL`. | Deploy the queue stack with `/ipa-deploy`, then run `make -f scripts/env.mk update-env-sqs` to populate `SQS_QUEUE_URL` in `.env`. |

## Next Steps

- **Run the full application locally** — see [Local Development](local-development.md) for running the FastAPI backend and React frontend
- **Explore the app-lib module structure** — see `app-lib/README.md` for feature-centric layout conventions and the `AbstractDataService` interface
- **Bedrock model reference** — consult the [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/) for supported models and API parameters
- **Tear down deployed infrastructure** — run `/ipa-destroy` to remove stacks when no longer needed
