---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The ECR stack is a prepare-lifecycle stack included automatically when selecting any stack that uses container images during `/ipa.compose`. Run the compose skill:

    /ipa.compose

The compose skill automatically includes ECR as a prepare dependency when the backend or queue stack is selected. The compose process generates a `scripts/prepare.mk` target for the ECR stack. Because it is a prepare stack, it is deployed once before the main application stacks and is not torn down during normal destroy operations.

## Configuration

The following `.env` variables map to the stack parameters:

| Parameter | `.env` Variable | Required | Default | Description |
|-----------|----------------|----------|---------|-------------|
| Namespace | `APP_NAMESPACE` | Yes | -- | Project namespace prefix for resource naming. Must match `^[a-z][a-z0-9-]{0,11}$`. |
| Environment | `APP_ENV` | Yes | -- | Deployment environment (e.g., `dev`, `staging`, `prod`). Must match `^[a-z][a-z0-9-]{0,11}$`. |

The repository name is derived as `{Namespace}-{Environment}-ecr`.

## Outputs

The stack exports the following values for use by other stacks:

| Output | Export Name | Description |
|--------|------------|-------------|
| RepositoryUri | `{StackName}-RepositoryUri` | ECR repository URI. Consumed by backend and queue tier stacks to resolve the Lambda container `ImageUri`. |
| RepositoryArn | `{StackName}-RepositoryArn` | ECR repository ARN. Available for scoping IAM policies or security controls to the specific repository. |
