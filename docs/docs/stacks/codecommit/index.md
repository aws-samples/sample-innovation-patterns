---
title: Overview
sidebar_position: 1
---

# CodeCommit

The CodeCommit stack deploys a single AWS CodeCommit repository for source code management. It serves as the source provider for the CodePipeline CI/CD stack, giving the project a fully managed Git repository within the AWS account. The stack supports optional KMS encryption at rest and is private by default with no public access.

**Template:** `infra/cfn/codecommit/codecommit.yml`
**Lifecycle:** prepare (one-time prerequisite stack)
**Capabilities:** none
**Composed via:** `/ipa-compose codepipeline`

## Features

- Fully managed Git repository within the AWS account
- Optional KMS encryption at rest via a customer-managed key
- Private by default with no public access configuration
- Customizable repository name and description

## When to Use

This stack is required when deploying the CodePipeline CI/CD stack. It provides the source repository that CodePipeline monitors for changes. Running `/ipa-compose codepipeline` auto-includes this stack as a transitive dependency and generates the `prepare.mk` targets. Any project that requires AWS-native source control should include this stack.
