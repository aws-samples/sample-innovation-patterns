---
name: ai-util-claude-skill
description: "Write new Claude Code skills from scratch given a description of what the skill should do. Use this skill whenever someone asks you to create a skill, write a SKILL.md, build a Claude Code plugin, make a reusable Claude workflow, or says anything like 'make a skill for X', 'I want Claude to always do Y', or 'create instructions for Z'. Also trigger when someone wants to turn a current conversation or workflow into a repeatable skill, or when they ask about skill format, structure, or best practices. Even vague requests like 'can Claude learn to do this?' or 'how do I teach Claude a process?' should trigger this skill."
model: opus
effort: high
---

# Skill Writer

You create high-quality, production-ready Claude Code skills. A skill is a set of instructions (and optionally bundled resources) that teaches Claude how to perform a specific task reliably and repeatably.

## Step 1: Understand What the User Wants

Before writing anything, clarify the skill's purpose. Extract or ask for:

1. **What should this skill do?** — The core capability in one sentence.
2. **When should it trigger?** — What would a user say or do that should activate this skill? Think broadly: direct requests, indirect signals, file types mentioned, keywords used.
3. **What does success look like?** — Expected output format, quality bar, files produced.
4. **What tools or dependencies are needed?** — Python libraries, npm packages, external APIs, specific file formats.
5. **Any edge cases or constraints?** — Things to watch out for, common failure modes, things the skill should never do.

If the current conversation already contains the workflow (e.g., the user says "turn what we just did into a skill"), extract answers from the conversation history — the tools used, the sequence of steps, corrections the user made, input/output formats observed.

Once you have a clear picture, summarize your understanding back to the user in a short bulleted list and **explicitly ask: "Do you have any questions or anything you'd like to change before I write the skill?"** Wait for their response before proceeding. Only move to Step 2 after the user confirms they're happy with the direction.

## Step 2: Write the SKILL.md

Every skill is a directory containing at minimum a `SKILL.md` file. Follow this structure exactly.

### File Structure

```
skill-name/
├── SKILL.md          # Required — the core instructions
├── scripts/          # Optional — executable code for deterministic tasks
├── references/       # Optional — docs loaded into context as needed
└── assets/           # Optional — templates, icons, fonts, etc.
```

### SKILL.md Anatomy

The file has two parts: YAML frontmatter and Markdown body.

```markdown
---
name: skill-name
description: "What the skill does and when to trigger it. Be specific and slightly pushy — Claude undertriggers skills by default, so cast a wide net of trigger phrases."
---

# Skill Title

[Markdown instructions for Claude to follow]
```

### Writing the Frontmatter

**name** — Lowercase, hyphenated identifier (e.g., `api-docs-generator`, `csv-cleaner`).

**description** — This is the single most important field. It controls whether Claude activates the skill. Write it as a single string that covers:
- What the skill does (1-2 sentences)
- Explicit trigger conditions — list specific phrases, keywords, file types, and contexts
- Near-miss exclusions if relevant — briefly note what this skill is NOT for, to prevent false triggers

The description should be "pushy" — slightly overinclusive rather than underinclusive. Claude tends to skip skills unless the description makes a strong case. Think of it as a search index: if a user's message doesn't match any words in your description, the skill won't fire.

**Example of a good description:**
```
"Generate professional API documentation from source code. Use this skill whenever the user mentions 'API docs', 'endpoint documentation', 'Swagger', 'OpenAPI spec', reference docs for a REST or GraphQL API, or asks to document routes, controllers, or service methods. Also trigger when the user has code files and says 'document this', 'write docs for this', or 'I need reference documentation'. Do NOT use for general README files or user guides — those are different deliverables."
```

**Example of a bad description:**
```
"Helps with documentation."
```

### Writing the Markdown Body

The body is what Claude reads when the skill triggers. Write clear, direct instructions in the imperative form. Here are the principles:

**Explain the why, not just the what.** Today's LLMs are smart — when they understand the reasoning behind an instruction, they generalize better and handle edge cases more gracefully. Instead of rigid rules with ALWAYS/NEVER in all-caps, explain the goal and let Claude reason about how to achieve it.

```markdown
<!-- Weak -->
ALWAYS use h2 headings. NEVER use h1.

<!-- Strong -->
Use h2 for section headings because the document title already occupies h1,
and duplicate h1 tags break document outline accessibility.
```

**Keep it under 500 lines.** If you're approaching this, add a layer of hierarchy: move detailed reference material into `references/` files and add clear pointers in SKILL.md about when to read them.

**Use progressive disclosure.** Structure the skill so Claude can get the high-level workflow quickly, then dive into details as needed:
1. Lead with a one-paragraph summary of the skill's purpose
2. Present the main workflow as numbered steps
3. Put detailed guidance, examples, and edge cases under each step or in reference files

**Include examples.** Concrete input/output examples are one of the most powerful tools for calibrating Claude's behavior. Format them clearly:

```markdown
**Example:**
Input: User uploads a CSV with columns "name", "email", "signup_date"
Output: Cleaned CSV with standardized date format, validated emails, duplicates removed
```

**Define output formats explicitly.** If the skill produces files, specify the exact structure:

```markdown
## Output Format
Generate a single `.docx` file with:
- Title page with project name and date
- Table of contents (auto-generated)
- One section per API endpoint
- Code blocks for request/response examples
```

**Handle errors and edge cases.** Anticipate what can go wrong and provide fallback instructions:

```markdown
If the uploaded file is not valid CSV (e.g., malformed rows, wrong encoding):
1. Attempt to detect and fix encoding (try utf-8, latin-1, cp1252)
2. If rows have inconsistent column counts, report which rows are malformed
3. Ask the user how to proceed rather than silently dropping data
```

### Writing Patterns Reference

**Workflow skills** — Use numbered steps for the main process, with substeps for details:
```markdown
## Workflow
1. Read the input file from `/mnt/user-data/uploads/`
2. Parse and validate the structure
   - Check for required columns: name, date, amount
   - Flag any missing or malformed values
3. Apply transformations
4. Write output to `/mnt/user-data/outputs/`
```

**Decision-tree skills** — Use conditional blocks when behavior branches:
```markdown
## Choosing the Output Format
If the user asks for a "report" or "document" → generate `.docx`
If the user asks for "slides" or "presentation" → generate `.pptx`
If the user asks for "data" or "spreadsheet" → generate `.xlsx`
If unclear, default to `.docx` and mention the other options.
```

**Template skills** — Define the exact structure Claude should produce:
```markdown
## Email Template
Subject: [Action Required] [Topic] — [Deadline]

Hi [Name],

[1-2 sentence context]. [Specific ask with deadline].

[Supporting detail if needed, max 2 sentences].

Best,
[Sender]
```

**Skills that bundle scripts** — If multiple test runs show Claude independently writing the same helper code, bundle it:
```markdown
## Generating the Chart
Run the bundled chart script rather than writing chart code from scratch:
\`\`\`bash
python /path/to/skill/scripts/generate_chart.py --input data.csv --output chart.png --style minimal
\`\`\`
The script supports styles: minimal, detailed, presentation. See `scripts/generate_chart.py --help` for all options.
```

**Multi-domain skills** — When a skill supports variants (e.g., AWS vs GCP), organize by domain:
```markdown
## Cloud Provider Setup
Read the appropriate reference file based on the user's target platform:
- AWS → read `references/aws.md`
- GCP → read `references/gcp.md`
- Azure → read `references/azure.md`

Then follow the deployment steps in that file.
```

### Thinking Depth Guidance

When writing skills, consider where deep reasoning improves output quality. Claude Code supports thinking keywords that control reasoning depth:

- `**ultrathink**` — ~32K token thinking budget. For steps where shallow analysis causes compounding downstream errors.
- `**megathink**` — ~10K budget. For medium-complexity analysis.
- `**think**` — ~4K budget. Default level.

**Decision taxonomy** — use this to decide whether a step warrants a thinking directive:

| Cognitive Demand | Effort Needed | Add Ultrathink? |
|-----------------|---------------|-----------------|
| File I/O (read, write, copy, create) | Low | No |
| Template filling (scaffold from answers) | Low | No |
| Q&A formulation (asking user questions) | Medium | No |
| Command dispatch (parse args, run tool) | Low | No |
| Format transformation (systematic rule application) | Medium | No |
| Gap detection (what's missing from a spec or context) | High | Yes |
| Architecture analysis (how something fits an existing system) | High | Yes |
| Adversarial review (finding problems, conflicts, risks) | High | Yes |
| Constitution/constraint checking (validating against rules) | High | Yes |
| HITL review formulation (identifying decision-worthy ambiguities) | High | Yes |
| Synthesis of complex findings (research docs, plans, as-built) | Medium-High | Consider |

**When to add ultrathink:**
- Adversarial self-assessment (review, validation, quality gates)
- Gap detection (completeness analysis across multiple dimensions)
- Architecture analysis (tracing dependencies and integration points)
- Constitution/constraint checking (cross-referencing multiple rule sources)
- HITL review formulation (distilling complex findings into actionable decisions)

**When NOT to add ultrathink:**
- File I/O operations
- Template scaffolding from user answers
- Q&A formulation
- Command dispatch or mechanical pipeline steps

**Directive format:**

Place the directive inline, immediately before the step that needs deep reasoning:

```markdown
**ultrathink** — <One sentence: what goes wrong with shallow analysis at this step.>
```

**Example:**

```markdown
**ultrathink** — Shallow review here means the skill ships with trigger gaps, unnecessary verbosity, or unexplained constraints that silently degrade quality.

## Step 3: Review and Refine
...
```

Most skills won't need ultrathink at all — mechanical workflows, template-based output, and command-dispatch skills should stay fast. Only add it where the cost of shallow reasoning compounds into downstream errors.

## Step 3: Review and Refine

**ultrathink** — Shallow review here means the skill ships with trigger gaps, unnecessary verbosity, overfitting to examples, or unexplained constraints. These are the most common skill quality issues, and they silently degrade every invocation.

After drafting the skill, review it with fresh eyes. Check:

1. **Would Claude trigger this correctly?** Re-read the description and imagine 5 different user messages. Would the skill fire for all of them? Would it falsely fire for unrelated requests?

2. **Is the flow clear?** Read the body as if you've never seen it before. Can you follow the steps without ambiguity? Every decision point should have a clear path.

3. **Is it lean?** Remove anything that isn't pulling its weight. If an instruction doesn't change Claude's behavior in a meaningful way, cut it. Verbose skills waste tokens and dilute the important parts.

4. **Are there examples?** At least one concrete example per major step or output format. Examples do more work than paragraphs of explanation.

5. **Is it general enough?** The skill will be used across many different prompts. Avoid overfitting to specific examples. Instructions should teach Claude the *pattern*, not memorize the *instance*.

6. **Does it explain the why?** For every instruction that constrains Claude's behavior, there should be a reason. If you can't articulate why a rule exists, it probably shouldn't.

## Step 4: Deliver the Skill

Create the skill directory and files:

```bash
mkdir -p /mnt/user-data/outputs/skill-name
# Write SKILL.md
# Add any scripts/, references/, or assets/ as needed
```

Present the completed `SKILL.md` to the user and explain:
- What the skill does
- How to install it (copy the directory to their skills folder, or package as `.skill`)
- How to test it (suggest 2-3 realistic prompts to try)

If the user wants to iterate, revise based on their feedback and re-test. The core loop is: draft → test → review → improve → repeat.

## Common Pitfalls to Avoid

- **Vague descriptions** — "Helps with X" won't trigger. Be specific about user phrases and contexts.
- **Overuse of ALWAYS/NEVER/MUST** — These feel authoritative but Claude responds better to understanding *why* something matters. Reserve all-caps for genuine safety constraints.
- **Giant monolithic SKILL.md** — If it's over 500 lines, split into references. Claude loads the whole body into context when the skill triggers, and overly long skills dilute focus.
- **No examples** — Abstract instructions are ambiguous. Examples disambiguate faster than any amount of explanation.
- **Overfitting to test cases** — The skill should generalize. If you find yourself adding narrow exceptions for specific inputs, step back and write a broader pattern.
- **Forgetting error handling** — Real users will provide unexpected inputs. The skill should guide Claude on what to do when things go wrong, not just when everything is perfect.
- **Ignoring progressive disclosure** — Don't dump everything at the top level. Lead with the workflow, then layer in detail. Use reference files for deep dives.