# IPA Process Skill Guidance

This document is the authoritative reference for writing process skills that execute reliably under agent control within the Innovation Patterns Agent (IPA). It is written for skill authors and contributors — technical practitioners already familiar with the IPA ecosystem — who need concrete, actionable guidance on producing skills that the builder executes correctly and consistently.

The design philosophy is direct: skills are instructions for an intelligent agent, not documentation for a human developer. Every structure, rule, and example in this document is optimized for how agents parse, reason about, and execute multi-step processes [11].

This document covers skill authoring patterns and techniques. It does not cover infrastructure pattern design, the eject workflow, or the Claude Code runtime.

## Core Principles

The following rules govern all skill authoring decisions. They appear first because every subsequent section builds on them.

### 1. The Context Window Is a Shared Resource

Every token in a skill competes with conversation history, user input, and other loaded skills for space in the agent's context window. The context window is not an aesthetic preference — it is a shared, finite resource [11].

The test for every line in a skill: "Does the agent need this? Can it derive this from general knowledge?" The builder is already knowledgeable about AWS services, infrastructure-as-code concepts, and common deployment patterns. A skill should not explain what CloudFormation is, what a VPC does, or how IAM works. Instead, it should provide the exact commands, exact validation criteria, and exact error recovery that the builder cannot derive from general knowledge [11].

**Concise** (~50 tokens):

```
Run: `aws cloudformation deploy --template-file vpc.yaml --stack-name ${APP_NAMESPACE}-${APP_ENV}-vpc`
Verify: Stack status is CREATE_COMPLETE or UPDATE_COMPLETE.
```

**Verbose anti-pattern** (~150 tokens):

```
CloudFormation is an AWS service that lets you define infrastructure as code.
We'll use it to deploy a VPC stack. The deploy command will create or update
the stack based on your template file. Make sure you have the right permissions...
```

The concise version provides exactly the information the builder does not already possess. The verbose version spends three times the tokens restating general knowledge [11].

### 2. Match Degrees of Freedom to Task Fragility

Not every instruction requires the same level of specificity. The degrees-of-freedom framework calibrates how tightly a skill constrains the builder's choices based on how fragile the operation is [11] [1] [3].

| Level | When to Use | IPA Example |
|-------|-------------|-------------|
| **High freedom** | Multiple approaches are valid; the correct choice depends on project context | Choosing which patterns to compose for an engagement |
| **Medium freedom** | A preferred approach exists, but some variation is acceptable | Configuring security group rules based on project requirements |
| **Low freedom** | The operation is fragile; consistency is critical; a specific sequence is required | CloudFormation deploy commands, IAM policy creation, resource provisioning |

Infrastructure operations are "narrow bridge with cliffs" territory — there is one safe path forward, and deviation causes real failures: misconfigured security groups, orphaned resources, deployment errors. Most IPA skill steps should be **low freedom**, with exact commands and exact verification criteria [11].

### 3. Progressive Disclosure Is the Architecture

The Anthropic skill authoring best practices establish a three-tier content architecture for managing skill complexity [11]:

1. **SKILL.md body** — under 500 lines; serves as the overview and primary navigation structure
2. **Reference files** — loaded on demand, one level deep from SKILL.md
3. **Utility scripts** — executed (not loaded into context); only their output consumes tokens

```text
ipa.deploy/
├── SKILL.md              # Main instructions (loaded when triggered)
├── VALIDATION.md          # Post-deploy verification steps (loaded as needed)
├── ROLLBACK.md            # Failure recovery procedures (loaded as needed)
└── scripts/
    ├── check-stack.sh     # Stack status check (executed, not loaded)
    ├── validate-deploy.sh # Post-deploy validation (executed, not loaded)
    └── rollback.sh        # Rollback script (executed, not loaded)
```

The critical rule: all references must be one level deep from SKILL.md. The builder may partially read files referenced from other referenced files, leading to incomplete information and unreliable execution. Deeply nested references are a structural anti-pattern [11].

## Skill Anatomy

Every IPA process skill follows a six-part skeleton. This structure is not a suggestion — it is the standard that the builder expects to encounter. Skills that deviate from this skeleton force the builder to spend tokens interpreting non-standard structure instead of executing the task [1] [2] [3] [4] [5] [6].

```markdown
---
description: "[What this skill does]. Use when [triggers]."
handoffs:
  - label: [Next Step Name]
    agent: [next.skill]
    prompt: [Prompt for next skill]
---

# [Skill Name]

## User Input

\`\`\`text
$ARGUMENTS
\`\`\`

Expected: [format description]

## Pre-Execution Checks

1. [Environment validation step]
2. [Prerequisite verification step]

## Execution Steps

1. [First action]
2. [Second action]
...

## Rules

- [Constraint that applies across all steps]
- [Another constraint]

## Completion Report

- Created: [file paths]
- Summary: [quantitative results]
- Next: [suggested next actions with exact commands]
```

### Frontmatter and Description

The `description` field is how the builder discovers a skill from potentially over 100 candidates. It must include both what the skill does and when to use it [11].

Write in third person — the description is injected into the system prompt alongside every other skill description. Include trigger words the user might say.

**Effective:**

```yaml
description: "Deploy CloudFormation stacks for the current IPA project, including VPC,
security groups, and application infrastructure. Use when the user says 'deploy',
'create infrastructure', 'stand up the stack', or invokes /ipa.deploy."
```

**Ineffective:**

```yaml
description: "Handles deployment."
```

The effective description enables accurate skill selection under ambiguous user input. The ineffective description forces the builder to guess [11].

### User Input Block

The user input block captures `$ARGUMENTS` with a MUST-consider instruction. It follows a standard pattern: display the raw input, state the expected format, and provide parsing guidance [1] [2].

```markdown
## User Input

\`\`\`text
$ARGUMENTS
\`\`\`

Expected: `[stack-name]` — the name of the CloudFormation stack to deploy.
If not provided, derive from `APP_NAMESPACE` and `APP_ENV` in `.env`.
```

### Pre-Execution Checks

Seven of nine speckit skills begin with environment validation before performing any substantive work [1] [2] [4]. IPA skills must do the same — particularly because infrastructure operations have side effects that are difficult or impossible to reverse.

Two approaches exist:

**Script-based detection** — for complex checks that involve multiple commands, external service calls, or branching logic. The script runs, returns structured JSON, and subsequent steps reference specific fields in the output [2].

```
1. Run `bash scripts/check-environment.sh`
2. Parse JSON output for `credentials_valid`, `region`, `existing_stacks`
3. If `credentials_valid` is false → STOP. Display: "AWS credentials are not configured.
   Run `aws configure` or set AWS_PROFILE in .env."
4. If `existing_stacks` contains the target stack → branch to update flow
```

**Inline validation** — for simple input checks such as regex patterns or enum membership. The ipa.init skill uses this approach: it validates each user-provided value against a regex pattern and displays an exact error message on failure [7].

Use scripts for complex detection (AWS credentials, existing infrastructure state). Use inline validation for simple input checks (format validation, enum membership) [2] [7].

## Writing Effective Instructions

This section covers the techniques that produce execution steps the builder follows correctly. Each technique is stated as a rule, followed by its rationale and a concrete example.

### Use Numbered Step Sequences

Steps must be numbered, not bulleted. Numbered steps imply sequence — the builder processes them in order, top to bottom. Bullets imply an unordered set, which the builder may process in any order [1] [2] [3].

Each step must contain a single primary action. Compound steps that combine multiple actions (do X and Y and Z) must be split into separate steps. Compound steps are a common source of partially completed operations: the builder may execute the first action and skip subsequent ones.

The Anthropic skill authoring best practices recommend providing a copy-paste checklist for complex workflows that the builder can track progress against [11]:

```
Deployment Progress:
- [ ] Step 1: Load .env configuration
- [ ] Step 2: Validate AWS credentials
- [ ] Step 3: Check for existing stacks
- [ ] Step 4: Generate deployment plan
- [ ] Step 5: Validate plan against constraints
- [ ] Step 6: Present plan for confirmation
- [ ] Step 7: Execute deployment
- [ ] Step 8: Verify stack completion
- [ ] Step 9: Run post-deploy validation
```

### Make Conditionals Explicit

Every conditional in a skill must be testable and complete. The pattern is: "If X, do A. If not X, do B." — never "consider doing A" [1].

Branch conditions must be testable — based on command exit codes, file existence, pattern matches, or parsed values. Subjective conditions ("if it seems like the stack is failing") are not testable and produce inconsistent behavior.

Every branch must have an explicit rejoin point. Without a rejoin, the builder may continue executing the branch indefinitely or skip subsequent steps.

```markdown
5. Check if the stack already exists:
   - Run `bash scripts/check-stack.sh ${STACK_NAME}`
   - Parse JSON output for `status`
   - If `status` is `NOT_FOUND` → proceed to Step 6 (create new stack)
   - If `status` is `CREATE_COMPLETE` or `UPDATE_COMPLETE` → proceed to Step 6 (update existing stack)
   - If `status` is `ROLLBACK_COMPLETE` → STOP. Display: "Stack is in ROLLBACK_COMPLETE state.
     Delete the stack with `aws cloudformation delete-stack --stack-name ${STACK_NAME}` and re-run."
6. [Both branches rejoin here]
```

### Specify Exact File I/O Contracts

Every step that reads or writes a file must name the exact file path, what to extract from it, and the exact output format. No step should say "read the relevant files" — that instruction is ambiguous and the builder may read the wrong files, wrong sections, or skip the step entirely [3] [4] [5].

**Vague:**

```
Read the project configuration and extract the deployment settings.
```

**Precise:**

```
1. Read `.env` from the project root
2. Extract: APP_NAMESPACE, APP_ENV, AWS_REGION, AWS_PROFILE
3. If any variable is missing → STOP. Display: "Missing required variable [name] in .env.
   Run /ipa.init to configure."
```

The precise version leaves no room for misinterpretation. The builder knows exactly which file, which values, and what to do if they are absent [3] [5].

### Provide Exact Command Strings

For low-freedom operations — which includes most infrastructure commands — provide the literal command string with variable substitution. Do not describe the operation in prose and leave the builder to construct the command [3] [6].

**Fragile:**

```
Deploy the stack.
```

**Robust:**

```
Run:
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name ${APP_NAMESPACE}-${APP_ENV}-vpc \
  --capabilities CAPABILITY_IAM \
  --region ${AWS_REGION} \
  --profile ${AWS_PROFILE} \
  --output json

If the command exits with code 0, verify the stack reached the expected state:

aws cloudformation describe-stacks \
  --stack-name ${APP_NAMESPACE}-${APP_ENV}-vpc \
  --query 'Stacks[0].StackStatus' \
  --output text \
  --region ${AWS_REGION} \
  --profile ${AWS_PROFILE}

Expected output: CREATE_COMPLETE or UPDATE_COMPLETE.
```

The robust version specifies the exact command, all required flags (including `--output json` or `--output text`), and the verification step. The fragile version produces inconsistent commands across executions [6] [11].

Always include `--output json` or `--output text` for AWS CLI commands. Without an explicit output format, the default may vary by environment configuration, producing unparseable results [3].

Address shell quoting edge cases explicitly. For arguments that may contain single quotes, provide the escape syntax: `'I'\''m Groot'` [3].

### Write for Agent Parsing, Not Human Reading

The builder scans for structure, identifies entry points, and executes linearly. Skills that embed critical instructions in flowing prose risk having those instructions skipped [1].

Three rules:

1. **Front-load the action.** State what to do first. Follow with rationale only if needed.
2. **Use tables for structured data.** Validation rules, error codes, and configuration parameters belong in tables, not paragraphs.
3. **Use numbered lists for sequences, bullet lists for unordered sets.** The format signals the expected processing order.

| Format | Agent Interpretation |
|--------|---------------------|
| Numbered list | Sequential — execute in order |
| Bullet list | Unordered — process in any order |
| Table | Structured data — look up by key |
| Prose paragraph | Background context — may be compressed or skipped |

## Verification Architecture

Reliable skills build verification into every stage of execution. IPA skills require verification at three levels: input validation, pre-flight checks, and post-execution verification [4].

### Input Validation Tables

For every user-provided input, define a validation pattern, an error message, and a recovery action. Present these as a table that the builder can apply mechanically [7].

| Variable | Pattern | Error Message | Recovery |
|----------|---------|---------------|----------|
| `AWS_REGION` | `/^[a-z]{2}-[a-z]+-\d+$/` | "Invalid region format — expected format like us-east-1" | Re-prompt for valid region |
| `APP_NAMESPACE` | `/^[a-z][a-z0-9-]{2,27}$/` | "Namespace must be 3-28 lowercase alphanumeric characters, starting with a letter" | Re-prompt for valid namespace |
| `APP_ENV` | `/^(dev\|staging\|prod)$/` | "Environment must be one of: dev, staging, prod" | Re-prompt with valid options |

The builder matches input against the pattern. On failure, it displays the exact error message and re-prompts. On success, it proceeds to the next variable. This pattern eliminates ambiguity in what constitutes valid input [7].

### Pre-Flight Checks

Before executing any infrastructure operation, the skill must verify that the environment is ready. This includes credential validation, existing state detection, and region confirmation [2] [3] [4].

Use scripts for complex pre-flight checks. The script returns structured JSON that subsequent steps reference by field name:

```bash
#!/bin/bash
# check-environment.sh — validates prerequisites for deployment

CREDENTIALS=$(aws sts get-caller-identity --output json 2>/dev/null)
if [ $? -ne 0 ]; then
  echo '{"ready": false, "error": "AWS credentials not configured or expired"}'
  exit 0
fi

ACCOUNT_ID=$(echo "$CREDENTIALS" | jq -r '.Account')
REGION="${AWS_REGION:-us-east-1}"

echo "{\"ready\": true, \"account_id\": \"$ACCOUNT_ID\", \"region\": \"$REGION\"}"
```

The script exits 0 even when credentials are invalid — because "not ready" is a valid state, not an error. The structured JSON output allows the skill to branch cleanly on the `ready` field [2] [11].

### Self-Check Loops with Iteration Caps

The validate-fix-repeat pattern catches errors that a single pass may miss. The pattern: run a validation check, fix any issues found, then re-run the check. The loop must have an explicit iteration cap to prevent runaway execution [2] [5] [11].

The speckit.specify skill demonstrates this pattern: after generating output, it runs a quality checklist, addresses failures, and loops a maximum of three times [1]:

```
Step 6b: Run Validation Check
  - For each checklist item, determine pass or fail
  - Document specific issues found (quote relevant sections)

Step 6c: Handle Validation Results
  - If all items pass → proceed to Step 7
  - If items fail → list failing items, update output, re-run check (max 3 iterations)
  - If still failing after 3 iterations → document remaining issues, warn user
```

The cap is not optional. Without it, the builder may enter an infinite loop attempting to fix an issue that is unfixable within the skill's scope [5] [11].

### Plan-Validate-Execute for High-Stakes Operations

For operations that create or modify infrastructure, the plan-validate-execute pattern is the strongest available safety mechanism. It catches errors before changes are applied, rather than after [11].

The pattern has six steps:

1. **Analyze** — read `.env` and detect existing infrastructure state
2. **Create plan** — produce a deployment plan (JSON or YAML) describing what will be created, modified, or deleted
3. **Validate plan** — run a script that checks for conflicts, missing prerequisites, and invalid configurations
4. **Present to user** — display the plan with a summary table and request explicit confirmation
5. **Execute** — run the actual infrastructure commands
6. **Verify** — confirm that resources were created correctly and the stack reached the expected state

This pattern is mandatory for any IPA skill that creates, modifies, or deletes infrastructure resources. It is a deliberate design choice: the builder produces a verifiable intermediate artifact (the plan), which both the validation script and the user can inspect before any side effects occur [11].

### Post-Execution Verification

After an operation completes, the skill must verify that it actually succeeded — not merely that the command returned exit code 0 [3] [6].

A CloudFormation deploy command may return 0 while the stack transitions to `ROLLBACK_IN_PROGRESS`. The exit code indicates that the command was accepted, not that the operation completed successfully.

```
8. Verify deployment:
   Run:
   aws cloudformation describe-stacks \
     --stack-name ${STACK_NAME} \
     --query 'Stacks[0].StackStatus' \
     --output text \
     --region ${AWS_REGION} \
     --profile ${AWS_PROFILE}

   Expected: CREATE_COMPLETE or UPDATE_COMPLETE
   If ROLLBACK_IN_PROGRESS or *_FAILED → STOP.
   Display stack events: `aws cloudformation describe-stack-events --stack-name ${STACK_NAME}`
```

Infrastructure operations must clearly distinguish between three categories [10]:

| Category | Safety Level | Example |
|----------|-------------|---------|
| **Read operations** | Safe to run at any time | `describe-stacks`, `list-resources`, `get-caller-identity` |
| **Write operations** | Require confirmation before execution | `deploy`, `create-stack`, `update-stack` |
| **Destructive operations** | Require explicit warning and confirmation | `delete-stack`, `remove security groups` |

## User Communication Patterns

Skills interact with users at defined points during execution. The following patterns establish how to collect input, report progress, and confirm actions.

### One Question at a Time

Present exactly one question per interaction turn. Presenting multiple questions simultaneously overwhelms the user and produces incomplete or ambiguous answers [5].

Each question must include four components:

1. A recommended option with reasoning
2. A table of all available options
3. Instructions for how to respond (letter, keyword, or custom input)
4. Validation of the response before proceeding

```
Select the deployment environment:

Recommended: **dev** — safest for initial deployment; no production impact.

| Option | Environment | Description |
|--------|-------------|-------------|
| A | dev | Development environment with minimal resources |
| B | staging | Pre-production environment mirroring production |
| C | prod | Production environment — requires additional confirmation |

Reply with A, B, C, or type a custom environment name.
```

### Confirmation Before Write

For any operation with side effects, the skill must display a summary of what will happen and request explicit confirmation before proceeding. The summary must include the source of each value so the user can verify that values originated where expected [4] [10].

```
Deployment Summary:

| Setting | Value | Source |
|---------|-------|--------|
| Stack name | myapp-dev-vpc | Derived from APP_NAMESPACE + APP_ENV |
| Region | us-east-1 | .env (user-configured) |
| Template | vpc.yaml | Auto-detected from patterns/ |
| Profile | dev-profile | .env (user-configured) |
| Capabilities | CAPABILITY_IAM | Required by template |

Proceed with deployment? (yes/no)
```

No skill should execute a destructive or expensive operation without this confirmation step. This is a deliberate design choice: the builder always gives the user the opportunity to catch misconfiguration before it becomes an infrastructure problem [4].

### Structured Completion Reports

Every skill must end with a completion report that includes three components [1] [2] [3] [4] [5] [6]:

1. **What was created** — exact file paths or resource identifiers
2. **Quantitative summary** — counts, percentages, or status values
3. **Next-action suggestions** — exact slash commands the user can invoke

```
## Completion Report

**Created:**
- Stack: myapp-dev-vpc (us-east-1)
- Outputs written to: .env (VPC_ID, SUBNET_IDS)

**Summary:**
- 1 stack deployed, 5 resources created
- Status: CREATE_COMPLETE

**Next steps:**
- Deploy security infrastructure: `/ipa.security`
- View stack resources: `aws cloudformation list-stack-resources --stack-name myapp-dev-vpc`
```

This report is not optional — it is how the user confirms that the skill succeeded and knows what action to take next [1] [6].

### Escape Hatches

Skills must respect early termination signals. The words "stop," "done," and "proceed" are standard escape hatches that allow the user to exit a loop or skip remaining optional steps [5].

A skill must never trap the user in a loop with no way out. If a skill collects input iteratively (such as clarification questions or configuration values), it must check for termination signals after each iteration.

## Script Design

Utility scripts absorb complexity that would otherwise clutter the skill body with multi-line bash sequences. Scripts execute — they are not loaded into context — so only their output consumes tokens in the context window [11].

The governing principle is "solve, do not punt." Scripts handle error conditions explicitly rather than failing and leaving the builder to interpret raw error output [11].

### Error Handling in Scripts

Scripts must handle every anticipated error condition and return structured output that the skill can process without further interpretation [2] [3] [11].

**Correct — handles errors, returns structured JSON:**

```bash
#!/bin/bash
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name "$1" \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null)

if [ $? -ne 0 ]; then
  echo '{"status": "NOT_FOUND", "message": "Stack does not exist"}'
  exit 0
fi

echo "{\"status\": \"$STACK_STATUS\"}"
```

**Incorrect — raw command, punts error handling to the builder:**

```bash
aws cloudformation describe-stacks --stack-name "$1" --query 'Stacks[0].StackStatus'
```

The correct version handles the "stack not found" case as a valid state and returns structured JSON. The incorrect version produces an unstructured AWS error message that the builder must parse and interpret, consuming additional tokens and introducing ambiguity [11].

### Exit Codes and Structured Output

Non-error states must exit 0 with a status field — not exit 1. A stack not existing is a valid state, not an error. An exit code of 1 signals to the builder that something went wrong, which may trigger unintended error recovery behavior [11].

All script output must be parseable JSON with documented fields. The skill should specify what fields the script returns and what values to expect:

```
Script: check-stack.sh <stack-name>
Returns JSON:
  - status: "NOT_FOUND" | "CREATE_COMPLETE" | "UPDATE_COMPLETE" | "ROLLBACK_COMPLETE" | other
  - message: Human-readable description of the state
  - outputs: (only when status is *_COMPLETE) Stack output values as key-value pairs
```

### Configuration Parameters

Every numeric constant in a script must have a documented rationale. No "voodoo constants" — unexplained numbers that future authors cannot evaluate or adjust [11].

```bash
# Wait up to 300 seconds for stack completion.
# Rationale: Simple CloudFormation stacks (VPC, security groups) typically
# complete within 3-5 minutes. 300 seconds provides margin for slower regions.
TIMEOUT=300
```

Without the rationale, a future skill author cannot determine whether 300 is a carefully chosen value or an arbitrary default. Documenting the reasoning enables informed modification.

## Anti-Pattern Catalog

The following pairs contrast common failure modes with their correct alternatives. The builder pattern-matches against examples more reliably than it interprets abstract rules — making paired examples the most effective training format [6] [11].

### Instruction Anti-Patterns

**1. Vague instruction vs. precise command**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Deploy the stack" | `aws cloudformation deploy --template-file template.yaml --stack-name ${APP_NAMESPACE}-${APP_ENV}-vpc --capabilities CAPABILITY_IAM --region ${AWS_REGION} --profile ${AWS_PROFILE}` followed by verification step |
| **Failure mode:** Inconsistent commands across executions; missing flags; no verification | **Result:** Identical execution every time; verification confirms success |

**2. Narrative prose vs. structured steps**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "First you should check if the stack exists, and if it does you might want to update it, otherwise create a new one. Make sure the credentials are valid before doing anything." | 1. Run `check-stack.sh`. 2. If `NOT_FOUND` → Step 3 (create). 3. If `*_COMPLETE` → Step 4 (update). 4. If `*_FAILED` → STOP with error message. |
| **Failure mode:** Builder may skip the credential check or misinterpret the branching | **Result:** Clear sequence with explicit conditions and branches |

**3. Compound step vs. single-action step**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Read the config, validate all values, and write the deployment plan" | 1. Read `.env` and extract `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`. 2. Validate each value against its pattern (see Input Validation table). 3. Write deployment plan to `deploy-plan.json`. |
| **Failure mode:** Builder may complete the first action and skip the rest | **Result:** Each action is atomic; partial completion is visible |

**4. Ambiguous file reference vs. exact path**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Read the relevant project files" | "Read `.env` from project root. Extract `APP_NAMESPACE` and `AWS_REGION`." |
| **Failure mode:** Builder reads wrong files or wrong sections | **Result:** No ambiguity; correct file and values every time |

### Structural Anti-Patterns

**5. Deeply nested references vs. one-level-deep references**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| SKILL.md references SETUP.md, which references CONFIG.md, which references DEFAULTS.md | SKILL.md references SETUP.md, CONFIG.md, and DEFAULTS.md directly |
| **Failure mode:** Builder partially reads files beyond the first reference level [11] | **Result:** All referenced content is reliably loaded |

**6. Too many options vs. one default with escape hatch**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Choose a VPC CIDR block. Options: 10.0.0.0/16, 10.1.0.0/16, 172.16.0.0/16, 192.168.0.0/16, or enter a custom CIDR." | "VPC CIDR: `10.0.0.0/16` (default). To override, set `VPC_CIDR` in `.env`." |
| **Failure mode:** Builder may stall choosing or present an overwhelming menu | **Result:** Sensible default proceeds immediately; override path exists |

**7. Inconsistent terminology vs. single term used everywhere**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| "Deploy the stack" / "create the infrastructure" / "provision the resources" / "launch the environment" used interchangeably | "Deploy the stack" used in every instance |
| **Failure mode:** Builder may interpret different terms as different operations | **Result:** One term, one meaning, no ambiguity |

**8. Missing pre-execution checks vs. validate-first skeleton**

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| Step 1 immediately begins deploying infrastructure | Step 1: Validate credentials. Step 2: Check existing state. Step 3: Confirm with user. Step 4: Deploy. |
| **Failure mode:** Deployment fails mid-way due to expired credentials or conflicting state [2] [4] | **Result:** Problems caught before any side effects occur |

## Workflow Integration

IPA skills connect to each other through frontmatter `handoffs` declarations that define the workflow graph. Each `handoffs` entry tells the builder (and the user) what skill comes next, preventing dead ends at the conclusion of a skill [2] [3] [5] [8].

The IPA workflow follows a defined sequence [8]:

```
ipa.init → ipa.security → ipa.compose → ipa.deploy → ipa.codepipeline
```

Each skill in this sequence has an **artifact contract** — the files and state it expects to find from the previous skill, and the files and state it produces for the next skill:

| Skill | Expects | Produces |
|-------|---------|----------|
| `ipa.init` | (none) | `.env` with project configuration |
| `ipa.security` | `.env` | IAM roles, log bucket, security outputs in `.env` |
| `ipa.compose` | `.env` with security outputs | CloudFormation templates in `infrastructure/` |
| `ipa.deploy` | Templates in `infrastructure/`, `.env` | Deployed stacks, stack outputs in `.env` |
| `ipa.codepipeline` | Deployed stacks, `.env` | CI/CD pipeline resources |

The `handoffs` frontmatter declares this contract explicitly:

```yaml
handoffs:
  - label: Deploy Infrastructure
    agent: ipa.deploy
    prompt: Deploy the CloudFormation stacks for this project
```

This enables the completion report to direct the user to the correct next step and ensures the builder understands the broader workflow context.

## Evaluation and Iteration

The Anthropic skill authoring best practices recommend an evaluation-first development approach [11]. Rather than writing a skill and hoping it works, authors should identify failure modes, create test scenarios, and iterate against measurable criteria.

The process has five steps:

1. **Identify gaps** — run the builder on representative tasks without the skill and document where it fails or produces incorrect results
2. **Create evaluations** — build three or more scenarios that test the identified gaps
3. **Establish baseline** — measure performance without the skill to quantify the gap
4. **Write minimal instructions** — add just enough instruction to pass the evaluations; resist the urge to over-specify
5. **Iterate** — test with real tasks, observe failures, and feed corrections back into the skill

The Claude A/B development pattern is particularly effective for IPA skills: one instance of the builder writes the skill (Claude A), while another instance tests it (Claude B). Observing where Claude B struggles reveals instructions that are ambiguous, incomplete, or misleading [11].

The Anthropic skill authoring best practices also recommend testing across model sizes (Haiku, Sonnet, Opus) to ensure that instructions are specific enough for smaller models while not being unnecessarily verbose for larger ones [11].

**Note:** No IPA-specific evaluation baselines exist at the time of this writing. Skill authors should create evaluation scenarios as part of developing each new IPA skill, using the five-step process above.

## Sources

1. speckit.specify — Feature specification creation with quality validation loop
2. speckit.plan — Implementation planning with research phases and constitution checks
3. speckit.implement — Task execution with phase-by-phase validation and progress tracking
4. speckit.analyze — Read-only cross-artifact consistency analysis with semantic modeling
5. speckit.clarify — Interactive ambiguity detection with structured Q&A and incremental spec updates
6. speckit.checklist — Requirements quality validation using paired correct/incorrect examples
7. ipa.init — Interactive `.env` configuration with validation tables, auto-detection, and confirmation-before-write
8. speckit.tasks — Dependency-ordered task generation with strict checklist format and story-based organization
9. speckit.constitution — Project constitution management with consistency propagation across templates
10. speckit.taskstoissues — GitHub issue creation from tasks with remote validation safety check
11. Anthropic, "Skill authoring best practices," Anthropic Documentation, 2025. https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices
