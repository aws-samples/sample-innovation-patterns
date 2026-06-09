---
name: ai-code-create
description: "Create a new feature specification folder with a README.md identity document. Use this skill when the user says 'create a feature', 'new feature', 'code create', 'start a new feature', 'add a feature spec', 'create spec folder', or wants to set up a new feature workspace. Also trigger when the user provides a feature description and wants a folder created. Do NOT use for initializing or refining project context (/ai-init) or generating research, plans, or code."
model: sonnet
effort: high
---

# Agent Code: Create Feature

You create a new feature specification folder and write a README.md identity document that establishes the feature's metadata, scope, and context for all subsequent pipeline skills.

## User Input

```text
$ARGUMENTS
```

The text above is the feature description. Use it to derive the folder name and README content.

## Step 1: Read the Context

Read `.context/README.md` from the project root.

- If the file does not exist:
  - Tell the user: "No project context found at `.context/README.md`. Run `/ai-init` first to set up your project context."
  - Stop. Do not create the folder without context.
- If the file exists: parse the YAML frontmatter and extract `output_path.ai-code` (default: `specs/`). Load the full context — you'll use it to enrich the README.

## Step 2: Get the Feature Description

If `$ARGUMENTS` is empty or contains only whitespace:
- Ask the user: "What feature do you want to create? Describe it in a sentence or two."
- Wait for their response.

If `$ARGUMENTS` has content, use it as the description.

## Step 3: Analyze the Description

The README you produce becomes the identity card that every downstream skill reads — getting the scope, requirements, and affected areas right here prevents compounding errors in research, planning, and implementation.

Before deriving a name, analyze the description to extract:
- **Feature name**: What the feature is called
- **Purpose**: Why it's being built (new capability, refactor, bugfix, optimization, migration)
- **Type**: New feature, enhancement, refactor, bugfix, optimization, migration, integration
- **Affected areas**: Which parts of the codebase this will touch (inferred from context + description)
- **Scope signals**: Any explicit inclusions or exclusions

## Step 4: Derive the Folder Name

**ultrathink** — Feature naming requires weighing existing naming conventions, potential collisions with established modules, and future discoverability. A poorly-chosen name becomes a permanent API surface.

From the analysis, extract the 2-5 most meaningful keywords:

1. Convert to lowercase
2. Remove articles and filler prepositions unless meaningful
3. Replace spaces/underscores with hyphens
4. Remove non-alphanumeric characters (except hyphens)
5. Collapse consecutive hyphens
6. Truncate to 50 characters at a word boundary

Examples:
- "User authentication with OAuth2 and Google login" → `user-auth-oauth2`
- "Refactor the payment processing pipeline" → `payment-processing-refactor`
- "Add rate limiting to the API" → `api-rate-limiting`
- "Fix the race condition in WebSocket reconnection" → `websocket-reconnect-fix`

## Step 5: Check for Conflicts

Check if `<specs_root>/<derived-name>/` already exists.

If it exists, use AskUserQuestion:
- "Use existing folder" — proceed (do not overwrite README.md)
- "Choose a different name" — ask for a new name

## Step 6: Create Folder and README.md

1. `mkdir -p <specs_root>/<derived-name>/`
2. Write `<specs_root>/<derived-name>/README.md`:

```
---
title: <feature-name>
---

# <Feature Title>

## Description
<1-2 sentences: what this feature does and why it's being built.
 Derived from description, enriched with context from .context/README.md.>

## Requirements
<Key functional and non-functional requirements inferred from
 the description and project context.>

## Affected Areas
<Which parts of the codebase this will touch. Inferred from
 the description and the Architecture section of .context/README.md.>

## Status
- [ ] Research
- [ ] Plan
- [ ] Implement
- [ ] Test
```

Write real content, not placeholders. The README is the feature's identity card — every subsequent skill reads it.

Note: Other specification artifacts may exist in this folder (from SpecKit or other tools) and can provide additional context.

### Validate README Completeness

After generating the feature README.md, verify semantic completeness:

- [ ] Description is specific to this feature (not generic)
- [ ] Requirements are actionable (each could become a plan phase)
- [ ] Affected Areas reference real paths or architectural layers
- [ ] Status checklist is present and all items unchecked
- [ ] No placeholder text remains ("[TBD]", "TODO", etc.)

IF any check fails: revise the README before proceeding.

## Step 7: Confirm and Guide

Tell the user:
```
Created feature: <specs_root>/<derived-name>/
Identity:  <specs_root>/<derived-name>/README.md

Next steps:
  /ai-code-research <derived-name>   — research the codebase for this feature
  /ai-code-plan <derived-name>       — create an implementation plan
  /ai-code-implement <derived-name>  — build the feature from a plan
```

## Step 8: Manifest Update

After creating the feature folder, update the specs manifest at `<specs_root>/README.md`:

1. Read `<specs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read the new feature's README.md — extract title, first sentence of Description, and last checked Status item
3. Append a new row to the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📐 (Design) → 📋 (Plan) → 🏗️ (Implement) → ✅ (Test)
5. Add the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
