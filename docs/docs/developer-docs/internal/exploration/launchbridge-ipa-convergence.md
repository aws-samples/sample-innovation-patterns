---
title: LaunchBridge / IPA Convergence
sidebar_position: 2
---

# LaunchBridge / IPA Convergence

## Executive Summary

The Innovation Patterns Agent (IPA) and LaunchBridge are two suites of Claude
Code skills — collections of instruction documents that Claude Code activates on
demand to perform a defined task. The two suites have grown adjacent but
separate. This document proposes merging IPA into LaunchBridge under a single
brand, and lays out a forward-looking approach for doing so.

The headline finding is that the two products are complementary, not
overlapping. LaunchBridge owns the application and evaluation layer — indexing,
governance, testing, prediction, metrics, and shipping — together with a mature,
multi-agent installer. IPA owns the infrastructure layer — composing and
deploying full-stack AWS environments — which LaunchBridge lacks entirely. The
merge direction follows directly from that asymmetry: LaunchBridge is the
chassis, and IPA is the missing engine.

Three problems make the merge non-trivial, and this document treats each
honestly rather than glossing over them: branding and command namespacing,
startup context budget across a large skill catalog, and avoiding collisions
between similarly named skills. All three are solvable with the Claude Code
plugin mechanism and the installer LaunchBridge already ships.

This is a direction-setting proposal. It makes the case for convergence,
describes the architecture at a high level, and surfaces the decisions that need
alignment. The implementation specification lives separately.

The three points to carry forward:

- **The suites are complementary.** Their capabilities barely overlap, so
  convergence is mostly additive — it adds capability rather than forcing
  features to be reconciled.
- **Package the result as a Claude Code plugin.** A plugin delivers command
  namespacing, one-step installation, and the ability to pay context cost only
  for the domains a customer enables.
- **Keep the supporting commitments lightweight.** Bring-your-own
  spec-driven-development and the installer technology choice are best handled
  with the smallest durable solution, not new machinery.

## Why Converge

IPA and LaunchBridge today differ in how their skills are invoked, and they
share no common distribution path. IPA skills are invoked by command name; many
LaunchBridge skills are triggered by keyword matches against their descriptions.
Keeping the two suites separate carries an ongoing cost: duplicated effort, the
risk of version drift on the assets they already share, and an incoherent story
for any customer who wants both infrastructure and evaluation capabilities in one
project.

Each suite has a single defining gap that the other closes. IPA can compose and
deploy infrastructure, but it has no installer — its skills are placed by
manually copying files into a project. LaunchBridge has a mature, multi-agent
installer with incremental updates, but it deploys no infrastructure of its own.
A merge closes both gaps at once. Because the two capability sets barely
intersect, the merge is mostly additive: the friction lies in naming, context
budget, and brand, not in conflicting features that must be reconciled.

### What Each Side Brings

The combined capability map shows near-zero overlap across every domain. Where a
surface looks like a collision, it resolves on inspection into two skills
operating at different altitudes.

| Domain | IPA | LaunchBridge | Relationship |
|---|---|---|---|
| Infrastructure compose and deploy | Yes — multiple stacks, generated Makefiles, CloudFormation and Terraform | None | IPA fills LaunchBridge's largest gap |
| Security | IAM role and permission provisioning | Static application security scanning | Complementary; different domains |
| CI/CD | Deploys AWS-native pipeline infrastructure | Scaffolds provider-agnostic CI configuration | Reconcilable; different altitude |
| Indexing and Q&A | None | Indexing and question-answering | LaunchBridge only |
| Test, evaluation, and metrics | None | Several evaluation and metrics skills | LaunchBridge only |
| Configuration and prompt registry | Deployment parameters | Application configuration registry | Different namespaces |
| Spec-driven development workflow | References it conceptually | Vendors and routes a shared workflow | Shared dependency |
| Multi-agent installer | None | Mature | LaunchBridge is the merge vehicle |

Two apparent collisions deserve a one-line resolution each. IPA's security skill
provisions IAM roles and permission boundaries, while LaunchBridge's security
skill aggregates static-analysis scanners — these are different problems, and a
converged suite keeps both. IPA's pipeline skill deploys an AWS-native pipeline
as infrastructure, while LaunchBridge's shipping skill scaffolds
provider-agnostic continuous-integration configuration — the same problem space
at different altitudes, reconcilable rather than conflicting.

There is exactly one true shared dependency: the family of skills that drives the
shared spec-driven-development and document workflow. Today it is referenced by
IPA and vendored by LaunchBridge. The merge should own it once, not twice.

## The Convergence Architecture

The merge rests on four forward-looking design decisions, each addressing one of
the hard problems named in the summary: how commands are namespaced, how context
cost is controlled at scale, how skills are distributed, and how the suite
accommodates whatever spec-driven-development framework a customer already uses.
Each is taken in turn below.

### Namespacing via a Claude Code Plugin

In Claude Code, a skill's invocation name comes from its directory name, and the
only way to produce a colon-separated command namespace is through a **plugin** —
a packaged bundle of skills (and optionally agents, hooks, and tool
configuration) that installs in one step. A plugin automatically prefixes every
command it contains with the plugin's name. Packaging the converged suite as a
plugin named `lb` therefore yields commands of the form `/lb:deploy`
automatically. Without a plugin, the achievable form is a flat command prefix
such as `/lb-deploy`, where the prefix is simply part of each skill's name.

Plugins are the right vehicle for reasons beyond the namespace. They install in a
single step, they carry a version, and they can be split into **sub-plugins** —
smaller plugins grouped by domain — so that a customer pays the startup context
cost only for the groups they enable. Whether the suite ships as one plugin or as
several domain sub-plugins is an open decision; the recommendation is deferred to
"Decisions to Align On."

### Context-Efficient, Just-in-Time Activation

Claude Code loads skills through **progressive disclosure**: at the start of a
session, only each skill's name and short description are loaded; the full
instruction body loads only when the skill is triggered or invoked. The
session-start cost is therefore small per skill — on the order of a few hundred
tokens of metadata — but it accumulates. A catalog approaching forty skills
costs a few thousand tokens at startup, measured against a listing budget that
defaults to a small fraction of the model's context window. When that budget is
exceeded, descriptions are shortened, which degrades the keyword matching that
auto-triggers skills.

The honest constraint is that Claude Code provides no native, path-conditional
skill gate. The intuitive goal of "show infrastructure skills only when the user
is working on infrastructure" has no first-class mechanism. The achievable
strategy is to group skills into domain sub-plugins, write precise descriptions
so triggering stays accurate, and — if needed — use session hooks to suggest
relevant skills. These numbers are guidance rather than hard limits; the right
move before committing to a single-plugin layout is to measure a real install
with Claude Code's diagnostics and confirm that no descriptions are being
truncated under budget pressure.

### The Installer as the Merge Vehicle

LaunchBridge's installer already solves the distribution problems IPA never
began. It maintains a registry of target agents and writes each agent's skills to
the correct location, so a single run can install for more than one agent. It
chooses between copying and symlinking depending on whether the install is for
active development or for delivery. It tracks a content hash per skill so that an
update re-copies only the skills that actually changed. It groups skills into
selectable bundles and supports non-interactive flags, which is precisely the
seam that makes "install some, not all" real today — at the granularity of a
single skill. It also exposes a provider hook for sourcing external skills, which
is the natural place for IPA's skills to plug in. Notably, the installer is the
most thoroughly tested asset across both repositories, which is itself an
argument for building the merge around it.

There is one open technology question. The installer is implemented in
JavaScript today. A Python-based install path — invoked as a tool installed
directly from a git repository — is a proven model for this class of tooling and
is attractive for ecosystem consistency. But it is a reimplementation of the
installer, not a thin wrapper: it would have to reproduce the agent registry, the
copy-and-symlink logic, content-hash diffing, and submodule resolution. The
existing installer already supports installation from a git repository and
incremental updates, so this is a strategic preference to cost out deliberately,
not an urgent capability gap.

### Bring Your Own SDD (BYOSDD)

**Spec-driven development (SDD)** is the practice of capturing a feature's intent
in structured specification files before implementing it, and several frameworks
exist for doing so. The requirement here is simple: a customer can plug in
whichever SDD framework they already use, or adopt a suggested default —
**openspec**, a lightweight, portable, open-source SDD framework.

The lightweight answer is that BYOSDD is a stance, not a piece of machinery, and
it rests on three inexpensive commitments. First, zero coupling: no converged
skill requires specification files to exist, so a customer using any framework —
or none — works without configuration. This property already holds today.
Second, a single optional setup question: during initialization, the suite asks
once whether to set up SDD, offering openspec as the recommended default, the
customer's own framework, or nothing — and acts only if openspec is chosen.
Third, a short note in the project's agent-context file telling the agent to
honor whatever specification artifacts are present by reading them as context.

The proof that this is sufficient is the repository itself: it already runs two
SDD dialects side by side with no adapter between them. That coexistence is the
strongest available evidence that the requirement needs a stance and a default,
not a routing layer.

## Decisions to Align On

These are the choices that need stakeholder buy-in. Each is listed with the
recommended option and a one-line rationale; the supporting argument lives in the
architecture sections above. The intent is to let readers agree quickly or
redirect deliberately.

| Decision | Recommended option | Rationale |
|---|---|---|
| Merge direction | Fold IPA into LaunchBridge | LaunchBridge has the installer, the multi-agent abstraction, and the test coverage; IPA has the missing infrastructure capability. |
| Plugin packaging | Multiple domain sub-plugins | Makes context cost opt-in by domain while still delivering the namespace. |
| BYOSDD shape | Stance plus optional openspec default | A routing manifest has no consumer today; zero coupling already works. |
| Just-in-time strategy | Sub-plugins plus precise descriptions | There is no native path gate; this is the achievable approximation. |
| Installer technology | Keep the current installer; defer the rewrite | It already does git-repo install and incremental updates; the rewrite is a preference. |
| Model coupling | Keep converged skills model-agnostic | Pinning a specific model undercuts the suite's multi-agent portability. |
| Shared-workflow ownership | Single source through the installer | Three owners of one asset invites version skew; consolidate to one. |
| First milestone | The plugin and namespace spike | Cheapest way to prove the namespace and measure context cost before committing. |

## The Path Forward

The path is phased so that the early, reversible work proves the foundations
before any commitment to brand or distribution model. The first two phases are
low-risk and can be undone; the later phases commit to the rebrand and the
distribution choice. Throughout, the Makefiles already delivered to customers
remain untouched — they carry no IPA-specific branding and depend on no IPA
tooling, so customer deployments are unaffected by the merge.

| Phase | Goal | Reversible |
|---|---|---|
| 1. Plugin and namespace spike | Prove the `/lb:` namespace and measure startup context cost across a representative skill subset. | Yes |
| 2. BYOSDD stance and default | Guarantee zero SDD coupling, add the one optional setup question, and add the agent-context note. | Yes |
| 3. Installer integration | Register IPA's infrastructure skills as a selectable group in the LaunchBridge installer. | Yes |
| 4. Rebrand | Replace IPA branding with LaunchBridge across skills, context, and documentation. | Largely |
| 5. Alternative install path (optional) | Provide a Python-based install path if the cost spike justifies it. | N/A |

The sequencing logic is deliberate. Phase 1 answers the single most consequential
architectural question — whether to ship one plugin or several — with measured
token numbers rather than estimates, and it does so before any brand work begins.
Phases 2 and 3 deliver customer-visible value (a clean SDD story and "install
some, not all") while remaining reversible. Only Phase 4 commits to the new
identity, and it is sequenced last among the required phases precisely so that the
foundations are proven first. Phase 5 is optional and gated on its own cost
assessment.

## What We Are Not Building (Yet)

A short, deliberate statement of what is out of scope keeps the proposal honest
and pre-empts over-engineering. Three items are explicitly deferred.

- **A structured routing layer for SDD frameworks.** No converged skill needs to
  read specification files uniformly across frameworks today, and the SDD tools
  drive themselves. Such a layer would add a maintenance surface that must track
  every framework's evolving commands, with no consumer to justify it. It should
  be built only if a concrete skill later needs uniform cross-framework access to
  specification artifacts.
- **The Python-based installer rewrite.** Deferred until a customer needs a
  Python-only install path. The existing installer already supports git-repo
  installation and incremental updates, so this is a preference rather than a
  gap.
- **Custom path-conditional activation hooks.** Building machinery to show
  infrastructure skills only inside infrastructure directories is speculative
  effort with no native support. Domain sub-plugins and precise descriptions
  cover the need without it.

## Risks and Open Questions

A proposal earns trust by naming risk plainly. The following are the substantive
risks the convergence carries, followed by the assumptions that remain
unvalidated.

**Risks.**

- **Namespace mechanics constrain the command form.** A true colon namespace
  requires packaging as a plugin; without one, the suite is limited to a flat
  command prefix. This decision shapes everything downstream and should be made
  early.
- **Context budget at scale.** A combined catalog approaching forty skills can
  trip the startup listing budget, shortening descriptions and degrading
  auto-triggering. Splitting into domain sub-plugins is the mitigation; there is
  no native path-conditional gate to fall back on.
- **Model-coupling divergence.** IPA pins a specific model; LaunchBridge stays
  model-agnostic for portability. A merge must choose, and pinning a model leaks
  Claude-specific assumptions into a suite that aims to be agent-agnostic.
- **Installer rewrite cost.** A Python-based install path is a real project, not
  a wrapper, and its effort is currently unestimated. It needs its own cost spike
  before any commitment.
- **Brand and identity churn.** Retiring the IPA brand means rewriting context
  files, skill descriptions, and documentation. The work is real and must be
  sequenced so that delivered customer Makefiles remain unaffected.
- **Shared-workflow ownership.** The shared SDD-and-document workflow currently
  has three owners. The merge must pick a single distribution path or risk
  version skew.

**Unvalidated assumptions.** Two assumptions underlie the proposal and are
product strategy rather than verified findings: that customers want multi-agent
support, and that customers want bring-your-own-SDD. Both should be confirmed
with stakeholders rather than treated as settled. The token and budget figures
cited throughout are documented guidance, not hard limits, and should be measured
on a real install before they drive a final layout decision.

## Recommendation

Convergence is the right direction: the capabilities are complementary, the merge
is additive, and LaunchBridge already provides the distribution machinery IPA
needs. The recommended first step is the lowest-risk one — a plugin and namespace
spike that proves the `/lb:` command form and measures real context cost — so
that the most consequential decision, single plugin versus domain sub-plugins,
rests on evidence. The supporting commitments around SDD and installer technology
should stay deliberately lightweight until a concrete need justifies more. With
alignment on the decisions listed above, the phased path can begin without
disturbing any customer already running delivered infrastructure.
