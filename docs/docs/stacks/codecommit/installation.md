---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The CodeCommit stack is auto-included when composing the codepipeline stack. It is a transitive dependency — selecting codepipeline automatically adds codecommit to the composition:

    /ipa-compose codepipeline

To deploy after composition:

    /ipa-prepare

The compose skill generates `prepare.mk` with the `prepare-codecommit` target and all required parameter wiring.

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
