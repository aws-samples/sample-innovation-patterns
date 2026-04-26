---
title: Overview
sidebar_position: 1
---

# Guides

Cross-cutting how-to documentation for tasks that span multiple IPA stacks or skills. Each guide follows the [Guide Format Standard](/developer-docs/docs/guide-format-standard) and addresses a single workflow goal.

All guides follow the IPA builder workflow sequence: compose, prepare, deploy, iterate, hand off.

- **[Composing a Solution](composing-solution.md)** — Select and assemble stacks into a deployable composition with generated Makefiles and wiring.
- **[Local Development](local-development.md)** — Run the FastAPI backend and React frontend locally against deployed AWS infrastructure.
- **[Notebook Development](notebook-development.md)** — Prototype and test with Jupyter notebooks connected to deployed resources.
- **[CI/CD with CodePipeline](codepipeline.md)** — Automate build, deploy, and test with CodePipeline executing the same Makefile targets.
- **[Extending with Skills](extending-with-skills.md)** — Author a custom stack skill and integrate it with `/ipa.compose`.
- **[Path to Production](path-to-production.md)** — Harden, document, and hand off a composition to the customer team.
