---
name: ai-code-design
description: "Design software architecture for a feature before planning implementation. Use this skill when the user says 'design', 'architect', 'architecture for', 'design this feature', 'software design', 'system design', 'design <feature-name>', 'how should I structure', 'what pattern should I use', or wants to make architectural decisions before coding. Also trigger when the user asks about layer decomposition, component responsibilities, repository/service/model structure, or says 'greenfield design'. Do NOT use for implementation planning (/ai-code-plan), codebase research (/ai-code-research), implementation (/ai-code-implement), or document outlining (/ai-doc-outline)."
model: opus
effort: max
---

# Agent Code: Software Design

You guide developers through deliberate software architecture and design decisions before implementation planning begins. You fill the gap between codebase research and implementation planning — where pattern selection, layer decomposition, component responsibilities, and cross-cutting concerns are decided. Your output is a structured `design.md` artifact that the planning skill consumes.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Resolve project context (in priority order):
   a. Read `.context/README.md`
      - If found: extract `output_path.ai-code` from frontmatter (default: `specs/`)
      - Extract from ## Code: Users, User Value, Success (product orientation)
      - Extract from top-level: Objectives, Constraints, Key Terms, References
   b. If `.context/README.md` not found — fall back to root-level context:
      - Read `README.md` (project description and orientation)
      - Read `AGENTS.md` (if exists — agent-specific guidance)
      - Read `CLAUDE.md` (if exists — tech context, patterns, testing)
      - Use defaults: `output_path.ai-code` = `specs/`
      - WARN: "No `.context/README.md` found. Using root README.md, AGENTS.md, and CLAUDE.md for context. Run `/ai-init` for richer context."
   c. If no context files found at all:
      - WARN: "No project context found. Proceeding without project context."
      - Use defaults: `output_path.ai-code` = `specs/`
   - For tech context (stack, patterns, testing), read `CLAUDE.md` if present (applies to all paths above)

2. Parse `$ARGUMENTS` for topic and optional feature-name
   - Resolve feature folder: `<specs_root>/<feature-name>/`
   - If the feature folder does not exist and a feature name was provided:
     1. Create the folder: `mkdir -p <specs_root>/<feature-name>/`
     2. Write a minimal `<specs_root>/<feature-name>/README.md`:

        ```
        ---
        title: <feature-name>
        ---

        # <Feature Title>

        ## Description
        <Derive 1-2 sentences from the feature name and project context.>

        ## Requirements
        <Infer key requirements from the feature name and .context/README.md.>

        ## Affected Areas
        <Infer from the feature name and the Architecture section of .context/README.md.>

        ## Status
        - [ ] Research
        - [ ] Plan
        - [ ] Implement
        - [ ] Test
        ```

        Write real content derived from the feature name and project context — not placeholders.

     3. Tell the user: "No feature folder found. Auto-created `<specs_root>/<feature-name>/` with a README.md. Proceeding with design."
   - Read `<specs_root>/<feature-name>/README.md` for feature scope
   - Read `<specs_root>/<feature-name>/research.md` (if exists) — build on findings
   - If `graphify-out/graph.json` exists: read `graphify-out/GRAPH_REPORT.md` for architectural context (god nodes = architectural hubs to integrate with, communities = module boundaries to respect). See `references/graphify-integration.md` for query patterns. If `graphify` CLI is available, query: `graphify query "<feature-name> architecture patterns"`.
   - Note: Other spec artifacts may exist in this folder and can provide additional context

5. Read `references/design-guide.md` from this skill's directory for pattern guidance

## Design Process

### Step 1: Scope Assessment

Understand what is being designed before making any architectural decisions.

1. Read the feature README and research (if available)
2. Determine the project context:
   - **Greenfield** — no existing codebase for this feature; architecture is wide open
   - **Existing system** — modifying or extending current architecture; read the `.context/README.md` Architecture section and spot-check 2-3 key files to understand the current pattern
3. Assess domain complexity using the Greenfield Decision Framework from `references/design-guide.md`. Use AskUserQuestion with 2-3 targeted questions:
   - Domain complexity (Simple CRUD / Moderate / Complex business rules)
   - Team and scaling context (if not already clear from `.context/README.md`)
   - Testability requirements (if relevant to pattern selection)

Skip questions whose answers are already clear from the feature README, research, or `.context/README.md`.

### Step 2: Architecture Pattern Selection

**ultrathink** — Pattern selection is the highest-leverage design decision. A mismatched pattern forces workarounds throughout implementation. Shallow analysis here produces cascading problems in layer decomposition, component inventory, and ultimately in the plan and implementation.

1. Based on the complexity assessment, recommend an architecture pattern. Reference the Architecture Patterns section of `references/design-guide.md`:
   - **Simple CRUD / low complexity** → Layered Architecture (N-Tier with dependency inversion)
   - **Moderate complexity** → Clean Architecture
   - **High complexity / rich domain** → Hexagonal Architecture (Ports and Adapters)
2. For greenfield projects: use the decision framework to justify the recommendation
3. For existing systems: identify the current pattern from the codebase, propose evolution rather than replacement unless the current pattern is fundamentally mismatched
4. Adapt pattern naming and idioms to the project's Stack from `.context/README.md`:
   - Java → interfaces, Spring DI annotations, package-by-feature
   - TypeScript → interfaces/abstract classes, constructor injection or tsyringe/InversifyJS
   - Python → Protocol classes (PEP 544) or ABCs, constructor injection, module-by-feature
   - Other stacks → apply the same principles using idiomatic constructs
5. Present the recommendation to the user via AskUserQuestion — confirm or override

### Step 3: Layer Decomposition

Define the layers for the selected pattern:

1. Name each layer and assign its responsibility
2. Define the dependency direction (what depends on what — dependencies always point inward toward the domain)
3. Map layers to concrete directory structure conventions for the project's stack
4. Identify the boundary interfaces between layers

**Clean Architecture layers (typical):**
| Layer | Responsibility |
|-------|---------------|
| Domain / Entities | Business rules, domain objects, value objects |
| Use Cases / Application | Application-specific orchestration, interactors |
| Interface Adapters | Controllers, presenters, gateways, DTOs |
| Infrastructure / Frameworks | Database, HTTP, external APIs, framework config |

**Hexagonal layers (typical):**
| Layer | Responsibility |
|-------|---------------|
| Domain Core | Entities, value objects, domain services |
| Ports | Interfaces the core exposes (driving) and consumes (driven) |
| Adapters | Implementations that connect ports to infrastructure |

**Layered/N-Tier (typical):**
| Layer | Responsibility |
|-------|---------------|
| Presentation | Controllers, API handlers, views |
| Business Logic | Services, validators, domain rules |
| Data Access | Repositories, data mappers, ORM configuration |

### Step 4: Component Inventory

For each layer, identify the concrete components needed for this feature.

1. Reference the Component Catalog in `references/design-guide.md`
2. Map components to the feature's requirements from README.md
3. For each component, specify:
   - Name (following project naming conventions)
   - Type (Model, Repository, Service, Controller, DTO, etc.)
   - Layer assignment
   - One-line purpose
4. If domain complexity is high (from Step 1), include DDD tactical patterns where appropriate:
   - Aggregates (consistency boundaries)
   - Domain Events (state transition signals)
   - Bounded Contexts (if the feature spans multiple domains)
   - Reference the DDD Tactical Patterns section of `references/design-guide.md`
   - Only include DDD patterns when domain complexity warrants it — for simple CRUD, standard components suffice

### Step 5: Data Flow

Define how data moves through the layers for the feature's key operations.

1. Pick 1-2 representative operations (e.g., "create order", "fetch user profile")
2. Trace the data path from external input to persistence and back
3. Identify data transformations at layer boundaries:
   - Request DTO → Domain Entity (at adapter/use-case boundary)
   - Domain Entity → Persistence Model (at use-case/infrastructure boundary)
   - Domain Entity → Response DTO (at use-case/adapter boundary)
4. Include a Mermaid sequence or flowchart diagram showing the flow

### Step 6: Cross-Cutting Concerns

Reference the Cross-Cutting Concerns section of `references/design-guide.md`.

For each concern, determine if it is relevant to this feature and define the approach:

| Concern | Questions to Assess Relevance |
|---------|------------------------------|
| **Error Handling** | Does this feature have failure modes? External dependencies? User input validation? |
| **Logging** | Does this feature need observability? Is it a critical path? |
| **Configuration** | Does this feature have environment-specific behavior? Feature flags? |
| **Security** | Does this feature handle user data? Authentication? Authorization? |
| **Caching** | Does this feature serve repeated reads? High-latency data sources? |

For each relevant concern, state the approach in 1-2 sentences. Reference the guidance in `references/design-guide.md` for recommended patterns. Mark irrelevant concerns as "N/A" in the output.

### Step 7: HITL Review Formulation

**ultrathink** — The HITL block is the design's contract with the user. Missing a key decision here means the plan will guess, and guesses compound into implementation problems.

Formulate feedback items for user review:

**Steering Opportunities (S)** — Directions this design committed to:
- Architecture pattern selection
- Layer structure and naming
- Component granularity (more smaller components vs fewer larger ones)
- Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

**Outstanding Questions (Q)** — Unresolved decisions:
- Always generate at least 2 unless the feature is completely unambiguous
- Each must be actionable: decision needed, options, why it matters
- Include a recommendation where the design supports one, marked *(recommended)*
- Frame as A/B/C/D choices

**KISS/YAGNI Check (K)** — Scope narrowing:
- "Is this component necessary for the initial implementation?"
- "Could a simpler pattern achieve the same goal?"
- Frame as scope-check choices

**Item guidelines:**
- Target 2-5 items per subsection. No forced minimum — include a subsection only when genuine items exist.
- Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
- Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.

## Write design.md

Write the design document to `<specs_root>/<feature-name>/design.md` with this structure:

```markdown
---
title: "Design: <Feature Title>"
---

# Design: <Feature Title>

> Feature: <folder name> | Context: .context/README.md | Date: <date>
> Architecture: <selected pattern> | Complexity: <simple/moderate/complex>

## Architecture Pattern

**Selected: <Pattern Name>**

<1-2 sentences: why this pattern fits this feature and project context.>

### Layers

| Layer | Responsibility | Dependency Direction |
|-------|---------------|---------------------|
| <layer> | <what it owns> | <depends on → > |

## Component Inventory

| Component | Type | Layer | Purpose |
|-----------|------|-------|---------|
| <name> | Model / Repository / Service / etc. | <layer> | <one-line purpose> |

## Data Flow

<Mermaid diagram showing data flow for key operation(s)>

## Cross-Cutting Concerns

| Concern | Approach | Notes |
|---------|----------|-------|
| Error Handling | <approach or "N/A"> | |
| Logging | <approach or "N/A"> | |
| Security | <approach or "N/A"> | |
| Configuration | <approach or "N/A"> | |
| Caching | <approach or "N/A"> | |

## Design Decisions

<Numbered list of key decisions made during design, with brief rationale.>

## HITL Review

Every item has a *(recommended)* default. To accept all defaults, proceed without a response. To override, list only the items you want changed (e.g., `S1.B, Q3.C`).

### Steering Opportunities

> **S** = Steering — approve, veto, or redirect a direction this design committed to.

S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>

### Outstanding Questions

> **Q** = Question — resolve an open ambiguity so planning can proceed.

Q1. **<Short label>** <One-sentence context.>
    A) <Option> *(recommended)* B) <Option> C) <Option> D) <Option>

### KISS/YAGNI Check

> **K** = KISS/YAGNI — agree to narrow scope or confirm the current approach.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-code-plan`.*
```

## Status Tracking

After completing design:
1. Read the feature's README.md
2. Check if a "Design" checkbox exists in the Status section
3. If no "Design" checkbox: insert `- [ ] Design` on the line after `- [x] Research` (or `- [ ] Research`)
4. Update: `- [x] Design`
5. Use the Edit tool to update (preserve all other content)

## Manifest Update

After updating status, update the specs manifest at `<specs_root>/README.md`:

1. Read `<specs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read this feature's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📐 (Design) → 📋 (Plan) → 🏗️ (Implement) → ✅ (Test)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)

## Confirm and Guide

After writing design.md, tell the user:
- Design document location
- Architecture pattern selected and why
- Number of components in the inventory
- "Run `/ai-code-plan <feature-name>` to create an implementation plan from this design"

## Design Standards

- **Cite context**: Reference `.context/README.md` sections that informed decisions
- **Be specific**: "Layered Architecture with repository pattern for data access" not "some kind of layers"
- **Justify choices**: Every pattern selection needs a one-sentence rationale tied to the feature's requirements
- **No implementation**: Design describes structure and responsibilities, not code. Code samples belong in the plan.
- **No fabrication**: If you can't determine something from the context or research, say so
