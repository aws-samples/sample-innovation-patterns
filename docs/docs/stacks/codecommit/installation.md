---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The CodeCommit stack is deployed automatically by the `/ipa-codepipeline` skill as a prepare-phase prerequisite. Run the codepipeline skill to provision both the repository and the pipeline:

    /ipa-codepipeline

The skill generates the prepare Makefile with all required parameter wiring for the CodeCommit stack.

## Configuration

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `Namespace` | String | Project namespace prefix for resource naming. |
| `Environment` | String | Deployment environment (e.g., `dev`, `staging`, `prod`). |
| `RepositoryName` | String | Name of the CodeCommit repository. Alphanumeric characters, dots, underscores, and hyphens only. |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `RepositoryDescription` | String | `IPA-managed source repository` | Human-readable description of the repository. |
| `KmsKeyArn` | String | *(empty)* | ARN of a KMS key for encryption at rest. When omitted, CodeCommit uses its default encryption. |

## Outputs

| Output | Description | Consumed By |
|--------|-------------|-------------|
| `RepositoryName` | Name of the created CodeCommit repository. | CodePipeline stack |
| `RepositoryArn` | ARN of the CodeCommit repository. | -- |
| `CloneUrlHttp` | HTTPS clone URL for the repository. | -- |
