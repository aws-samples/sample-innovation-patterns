# ADR Format Reference

Shared normative reference for the **decision log** — the directory of architectural decision records (ADRs) a project keeps, one short markdown file per architecturally significant decision. "Decision log" is `adr.github.io`'s own term for the collection, so this reference uses it rather than inventing a synonym.

`/ai-adr` writes and transitions records against every rule here. `/ai-plan` and `/ai-implement` need only the log-path resolution rule (§11), the five states (§5), the four reader tolerances (§6), and the status-to-authority mapping (§15) — they read a status and never write one.

The length budget (§16) and the provenance rule (§17) are **writer-only**, and named as such here so no consumer starts enforcing them. A reader that applied a 450-word cap or looked for a ` — *(inferred)*` marker would reject records already committed to the log — including AWS-shaped records written before this reference existed — and a consumer that never writes a record has nothing to gain from either rule.

Every rule cites the page or the script that establishes it. §14 names the two rules that are inferences rather than specifications.

| Source | Where |
|---|---|
| AWS process | `docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html` |
| AWS best practices | `…/architectural-decision-records/best-practices.html` |
| AWS FAQ | `…/architectural-decision-records/faq.html` |
| AWS appendix | `…/architectural-decision-records/appendix.html` |
| adr-tools | `github.com/npryce/adr-tools` v3.0.0 — cited by script name (`_adr_title`, `_adr_status`, …) |
| Nygard's template | the published template whose status list ends in "etc." |

`adr(1)`, the Ubuntu man page, is authority for the **command surface** only: its BUGS section calls the page a stub, and it names no directory, no `.adr-dir`, and no filename convention. Never cite it for a path.

## §1. When a decision earns a record

Write a record only for a decision affecting one of five categories, which AWS quotes from Richards and Ford 2020 (AWS process): **structure** (patterns such as microservices), **non-functional requirements** (security, high availability, fault tolerance), **dependencies** (coupling of components), **interfaces** (APIs and published contracts), **construction techniques** (libraries, frameworks, tools, processes).

Without the test, an agent asked to write an ADR writes one for any decision at all, and a log of fifty unrankable records is a log nobody reads.

## §2. The record's sections

AWS's example record (AWS appendix), in order: **Title**, **Status**, **Date**, **Context**, **Decision**, **Consequences**, **Compliance**, **Notes** (Author, Version, Changelog).

Compliance and Notes are AWS-specific and both mandatory — the AWS FAQ requires that "Each ADR must have a status and a changelog that contains the change date and the person who is responsible for the change", and Compliance records how adherence is verified.

**Considered alternatives go inside Context**, not in a section of their own: "The context should mention possible solutions the team considered" (AWS appendix). MADR's separate `## Considered Options` is a structural deviation — do not borrow it.

AWS's set is a **superset** of adr-tools' packaged template, which is Nygard's five sections (Title, Status, Context, Decision, Consequences) and nothing more. Adopting AWS therefore costs no interoperability, while adopting adr-tools' template would drop the two sections the FAQ mandates.

**Bullets are the default shape inside four sections** — Context, Decision, Consequences, and Compliance — under the per-section caps §16 fixes. This changes the shape of what goes inside four sections and changes the section set itself in no way: all eight stay mandatory, and considered alternatives stay inside Context rather than moving to a list of their own.

**The one place a bullet is illegal is the `## Status` keyword line.** `+ Accepted` is not exactly equal to `Accepted`, and `_adr_remove_status` deletes only the line *exactly equal* to the keyword — so a bulleted status survives removal untouched, a later supersession appends `Superceded by [...]` beneath it, and the record then asserts two states at once with nothing erroring anywhere. The status keyword sits alone on its own bare line, always (§4, constraint 4).

## §3. The Decision prose rule

AWS process: "The decision must clearly state, in imperative language, the solution the team has decided to adopt. Avoid using words such as 'should,' and phrase each decision to say 'We use…' or 'The team has to use…'"

Write `We use Postgres 16 for the ledger.` Reject `should` in this section — a decision phrased as a recommendation cannot be enforced, because nothing in it says the team is bound.

**The rule applies per bullet, not per section.** Once Decision is a list (§2), each bullet opens `We use` or `The team has to use`, and each is checked for `should` on its own. A section whose first bullet reads `We use Postgres 16 for the ledger` and whose second reads `we should probably pin the minor version` holds one decision and one suggestion, and the pinned version binds nobody.

## §4. Four positional constraints

adr-tools parses records with `head`, `cut`, and `awk` rather than a markdown parser, so its expectations are positional. A record that breaks one still renders in a browser while producing wrong output from a tool, which is why each constraint names its failure.

1. **First line is `# Title`, with no YAML frontmatter above it.** `_adr_title` is `head -1 | cut -c 3-`, so a leading `---` makes every title in a generated table of contents the two characters after the delimiter — in practice `-`. This is the constraint with teeth: MADR puts its metadata in frontmatter, so MADR's structure and adr-tools' tooling cannot both be used.
2. **`Date: YYYY-MM-DD` on the next content line.** adr-tools' template emits `Date: DATE` and substitutes `date +%Y-%m-%d`. No script parses the field, so this is convention rather than mechanism — it costs one line and matches AWS's Date section.
3. **Status is bare prose inside a `## Status` section, never a `Status: X` field.** `_adr_status` returns every non-blank line between `## Status` and the next heading. A record that writes the status as a field, or in frontmatter, is invisible to `adr` and to any parser modelled on it.
4. **The status keyword sits alone on its own line.** `_adr_remove_status` deletes the line *exactly equal* to the keyword, so `Accepted 2026-08-22` survives removal untouched: a later supersession appends `Superceded by [...]` and leaves the accepted line in place, and the record then asserts two states at once with nothing erroring anywhere. An acceptance timestamp goes on a separate line inside `## Status`, or in the changelog — never appended to the keyword.

## §5. The five states

| State | Source |
|---|---|
| `Proposed` | AWS process — the owner "provides the ADR in the **Proposed** state at the beginning of the process" |
| `Accepted` | AWS process; also the literal adr-tools substitutes at creation |
| `Rejected` | AWS process |
| `Superseded` | AWS process |
| `Deprecated` | Nygard's template |

Every value is published vocabulary, so this format **adds no status of its own** and has no status deviation to defend.

**Five states and no sixth.** A parking state — the one a user reaches for when a proposal is going nowhere and neither accepting nor declining it is true — was researched, recommended, and declined on 2026-08-20. No published ADR source names such a state, so adding it would put the set's only invented value in it; there is no verb for it either. The accepted cost: a proposal nobody reviews warns on every planning run until someone accepts it, declines it, or deletes it.

## §6. Reading a status — four tolerances

Every consumer applies all four. Each prevents the same failure, a **retired decision read as live**, which under §15's mapping stops a plan to comply with a decision the team already replaced.

1. **Match both spellings of superseded.** adr-tools writes "Super**c**eded" — `adr-new`'s supersede path calls `_adr_add_link "$target" "Superceded by"`. Match `Superseded` and `Superceded`.
2. **A supersession link with no keyword is superseded.** `_adr_remove_status` deletes the old keyword outright, so the retired record's Status section holds only `Superceded by [Title](file.md)` — no `Accepted` and no `Superseded` token for a keyword lookup to find.
3. **Read status as the prose body of `## Status`,** not as a field.
4. **Take the keyword case-insensitively from the section's first non-blank line.** A correctly-written record legitimately holds more than one line there — a keyword plus a link, or a keyword plus a timestamp — so a reader requiring exactly one line misreads it.

An unrecognised keyword is **reported once, naming the file and the value, and loaded as no constraint**. Both silent defaults fail: reading it as `Accepted` turns a typo into a hard gate on a decision nobody made, and reading it as absent lets a real decision quietly stop gating.

## §7. Immutability, as AWS scopes it

Two sources disagree, and the difference decides whether a lifecycle is implementable at all:

- **log4brains, unconditional:** "an ADR is immutable. Only its status can change."
- **AWS, scoped to post-acceptance (AWS best practices):** "The team should treat ADRs as immutable documents after the team accepts or rejects them."

Under log4brains' reading, AWS's own rework loop is illegal, because revising a `Proposed` record's Context mutates something other than its status. **This format follows AWS** — it is the authority this format traces to, and it names the boundary instead of implying one. The rule that follows:

- A **`Proposed`** record is a working document. Context, Decision, Consequences, and Compliance may be revised in place.
- An **`Accepted`** or **`Rejected`** record is frozen. Only the keyword and link lines inside `## Status` may change.

## §8. Transition legality, and the three refusals

A record is freely editable while `Proposed`; once `Accepted` or `Rejected` the only moves left are `Accepted → Superseded` and `Accepted → Deprecated`; every other change is a new record.

Two transitions are **refused as illegal moves**, and each refusal offers supersession or deprecation as the legal alternative:

- **`Accepted → Rejected`.** "Decline the X decision" is how a user asks to undo an accepted decision, and a silent status edit turns "we decided this and later changed our minds" into "we never decided this" — it erases the fact that the team decided it.
- **`Rejected → Accepted`.** The same boundary, other direction.

Deprecation is the move for an accepted decision that no longer applies with nothing replacing it. Without that state such a record has no legal move at all, which is why it is kept.

The third refusal is **distinct in kind** from those two, and confusing the two kinds produces the wrong message to the user. `Accepted → Rejected` and `Rejected → Accepted` are illegal moves — no input makes them legal. This one blocks a *legal* move on unresolved content:

- **`Proposed → Accepted` and `Proposed → Rejected` are refused while any bullet still carries ` — *(inferred)*`,** the marker §17 puts on a claim the agent concluded rather than read or was told. Acceptance must leave Context, Decision, Consequences, and Compliance byte-identical (§7), so the marker cannot be stripped during the transition — accepting with one in place freezes an unconfirmed claim into a record that then gates every plan under §15's mapping. The resolution is to confirm or drop the claim while the record is still `Proposed` and freely editable, then transition. The refusal names each unresolved bullet, so the user does not have to open the file to find them.

`Accepted → Superseded` and `Accepted → Deprecated` are outside this refusal: by it, an `Accepted` record holds no marker to find.

## §9. Immutability and the changelog, reconciled

The AWS FAQ mandates a changelog on every record; AWS best practices says where a change goes: "change the status of the old ADR to **Superseded**, note their changes in the change history of the *new* ADR, and keep the old ADR in the decision log."

So a change is recorded in the **new** record's changelog while the old record's status becomes `Superseded`. An agent that appends the explanation to an accepted record's own changelog has violated immutability while appearing to honour the changelog mandate. adr-tools implements the same reconciliation — its supersede path edits the old record's Status section and nothing else.

## §10. Who sets a status

**No skill sets a status on its own initiative.** A record moves only on an explicit human instruction.

One sanctioned exception: `/ai-adr` writes the log's own first record as `Accepted` on its first run in a repository, because invoking it on a repository with no log *is* the decision that record documents. `adr init` does the same. This is not a licence to self-accept anywhere else.

## §11. Resolving the log path, and creating a log

Two rules, deliberately different. Conflating them creates a second log beside the one a project already has.

**RESOLUTION — every consumer.** Mirroring adr-tools' `_adr_dir`, walking up from the working directory and at each level:

1. **`.adr-dir` present** → its contents, resolved relative to the level that held it. Stop.
2. **an existing `doc/adr` directory** → that path. Stop.
3. otherwise ascend; at the filesystem root, **no log exists**.

Resolution ends at "no log exists", **not at a default path**. `_adr_dir` itself ends with a bare `echo doc/adr`, but a consumer handed a directory holding no records gains nothing from it, so every consumer treats the third outcome as *skip*.

**CREATION — `/ai-adr`'s first-run branch alone.** A new log goes at **`docs/adr`**, and `.adr-dir` records that path immediately.

**Why the two paths differ.** The probe reads `doc/adr` because that is where `adr init` with no argument writes, and where it writes no `.adr-dir` — so probing it is the only thing standing between a project that already keeps records there and a duplicate log at `docs/adr`. Creation uses the plural form because it matches the `docs_path` and `output_path` keys a project already has.

**`.adr-dir` is the only carrier of the log path.** It is `adr-init`'s own one-line file (`echo "$1" > .adr-dir`), an ordinary tracked file, so the path survives a fresh clone; `cat` is the whole parser; and the `adr` CLI honours it, so `adr list` works in a log these skills created. No frontmatter key participates — `.context/README.md` holds nothing about the log, so `/ai-init` needs no change. Claim it as "the convention of adr-tools, the most widely packaged ADR toolchain, committed in roughly 300 public repositories", never as an ecosystem standard: no second tool reads it.

**Where a created log lands.** `docs/adr` nests inside a detected `docs_path` for Docusaurus, MkDocs, Jekyll, and the heuristic fallback, so in most consuming projects the records are published to the site, become sidebar entries, and fall under the link check that gates the docs build. Say so once on the first run, and name `doc/adr` as the alternative for a project that wants the log unpublished.

## §12. Filenames — a named deviation

Records are named `YYYY-MM-DD-description.md`. AWS specifies no filename convention, and `adr.github.io` — the source AWS refers naming to — specifies none either, so this deviates from no authority. It does diverge from the ecosystem's dominant sequential-number convention, so it is recorded here as a deviation with its costs.

- The **date is the creation date**, written once and never rewritten, matching `manifest-update.md:73` — the leading position is always the date, never a sequence number. Renaming on acceptance would break every inbound link and would itself mutate a record whose value is that it does not move.
- **Accepted downside: no short citable identifier.** Cross-references carry the full filename or the title, and number-keyed tooling does not apply — `adr-log`, the Backstage ADR plugin, and `@ADR(n)` annotations all key on the number.
- **Accepted downside: `adr new` must not be run.** Its allocator is `ls | grep -Eo '^[0-9]+' | sed -e 's/^0*//' | sort -rn | head -1`, so in a dated log the maximum is the *year*: a 2026 log yields `2027-<slug>.md`, sorting between real dates, with nothing erroring. Create records with `/ai-adr`; use the CLI for `list`, `generate toc`, `generate graph`, and `link` only. `adr upgrade-repository` is untested here and excluded as a precaution rather than a demonstrated hazard.
- On a **same-day slug collision**, ask. Never overwrite.

## §13. The index

The log's index is **`<log>/README.md`**: a table of Date, linked title, and Status, listing **every record including retired ones** — a rejection an agent cannot see is a rejection it proposes again.

`/ai-adr` maintains it on every write and every transition, carrying the same update-on-every-write obligation the working manifest does (`manifest-update.md`). It must be a **committed file** rather than generated on demand, because what routes an agent to it reads a file from disk and cannot run a command.

`adr generate toc` is useful as a drift check, but it emits `* [$title]($link)` with **no status column** — so a check extracts titles and links from both sides before diffing, or it reports a difference on every run and gets ignored.

## §14. Two labelled inferences

The changelog itself is an **AWS mandate** (AWS FAQ). Two rules about its contents are **inferences from AWS's example rather than specifications**, and are presented as such wherever they appear:

- **Bumping the version to `1.0` on acceptance.** AWS mandates a version and shows `0.1: Initial proposed version`, but never states the bump.
- **Putting the rejection reason in the changelog row.** AWS requires the reason — the owner "adds a reason for the rejection to prevent future discussions on the same topic" — and does not say where it goes.

## §15. Consumers: absence is normal, and status maps onto the existing ladder

A project with **no log is the normal case** for `/ai-plan` and `/ai-implement`. Both skip **silently** — a warning on every run in a project that has made no architectural decisions is noise.

When a log resolves, each record's status maps onto the constraint authority ladder those skills already run for the `*(inferred)*` marker. No second mechanism:

| Status | Authority |
|---|---|
| `Accepted` | Behaves as a **confirmed** constraint — stop and revise |
| `Proposed` | Behaves as an **inferred** constraint — warn, name the record, continue |
| `Rejected`, `Superseded`, `Deprecated`, log4brains' `draft` | Not a constraint. Load nothing, print nothing |
| anything else | Not a constraint, reported once with the filename and the value (§6) |

Name the record **by filename** in every warning and every stop, so the user can open it. There is no short identifier to cite — that is §12's accepted cost.

## §16. Record altitude — the length budget

**Writer-only.** `/ai-adr` obeys this section; no consumer enforces it.

"One short markdown file" is an adjective, and an adjective loses to any specific rule pointing the other way. So the budget is numbers:

| Section | Cap | Shape |
|---|---|---|
| Context | 6 bullets | one per constraint; one per rejected alternative, with its reason on the same bullet |
| Decision | 5 bullets | each opens "We use" — §3's phrasing rule survives bulleting unchanged |
| Consequences | 6 bullets | each outcome bullet prefixed `Positive:` or `Negative, accepted:`, at least one of each; a bullet carrying §17's marker states an unresolved risk and takes the marker in place of a prefix |
| Compliance | 4 bullets | each a real check, or the literal `Not yet defined: <what is unverified>` |
| Any bullet | 30 words | one claim plus one consequence clause |
| The four body sections together | 450 words | headings excluded. Notes sits outside the budget: Author, Version, and the Changelog are AWS-fixed structure whose rows carry a date, a person, and a reason |

A **prose paragraph** is permitted only where a bullet cannot carry the claim, and at most one per section. Two paragraphs in a section is the section reverting to prose.

**The altitude, stated because `voice.md` reads like a prohibition on this.** That standard requires preserving analytical depth — "compress the prose, never the analysis" — and states that removing a concept to satisfy it is a failure of it. At record altitude the depth rule is satisfied by **naming a consequence in a clause rather than explaining it in a paragraph**: the concept is kept, the paragraph is not. A record states a decision and what follows from it; the reasoning that produced it lives in the interview the record came out of and in whatever artifacts the project keeps.

**The cut-order.** A budget met by deleting a real accepted downside is worse than an over-long record, so what gets cut is specified rather than left to judgement.

Cut first, in this order:

1. **Content restating this reference's own mechanics.** A record explaining why `adr new` allocates from the calendar year duplicates §12 at the reader's expense — and the duplication compounds, because the record and the reference then drift apart.
2. **Editorial connectives** — "it is worth noting that", "with that said", a sentence whose whole job is introducing the next one.
3. **The same fact stated in two sections.** Keep it where it is load-bearing and drop the echo.

Never cut:

- **A rejected alternative and the reason it was rejected.** AWS requires Context to mention the solutions the team considered, and a rejection an agent cannot see is a rejection it proposes again.
- **An accepted downside.** A record listing only upsides reads as advocacy, and the downside is the part a reader years later cannot reconstruct.
- **A consequence for the planning pipeline** — what `/ai-plan` and `/ai-implement` do differently once this record is `Accepted` (§15).

**No offloading.** A record stays self-contained on its project-specific content, so it cannot meet the budget by citing a pipeline artifact for its reasoning: `/ai-archive` retires working folders into `.archive/`, and a project may gitignore its working root outright, so the cited path may be absent from a fresh clone and the record then points at nothing. Citing a source file by `path:line` is different and encouraged — that is code, and it ships with the clone.

## §17. Provenance of a record's claims

**Writer-only**, like §16.

A record is read years later by someone holding none of today's context, so a claim the agent concluded and a claim the user supplied must not look alike on the page. Every bullet in a record falls into one of three classes:

| Class | How it appears | Example |
|---|---|---|
| The user said it | plain bullet, no marker | "the team has no operational experience with it" |
| A file shows it | plain bullet carrying a `path:line` citation, which is itself the provenance | "`infra/main.tf:1-40` declares none" |
| The agent concluded it | bullet suffixed ` — *(inferred)*` | "Query latency under the reporting load is untested at this size — *(inferred)*" |

**Silence means confirmed**, matching `/ai-init`, where an unmarked constraint bullet is a confirmed one and a derived one carries the suffix. That default is safe only under the strict converse, which is the rule: **an unmarked bullet must trace to the user's words or to a cited `path:line`**, and anything that traces to neither takes the suffix.

**The literal suffix is ` — *(inferred)*`** — em dash, a space either side of it, the word italicised in parentheses. It is the spelling `/ai-init` writes (`ai-init/SKILL.md:126`) and the one its Refine Mode deletes on confirmation, so this reference introduces no second vocabulary and a user who has met the marker in `.context/README.md` already knows what it means and how it clears.

**A marker is resolved while the record is `Proposed`** and therefore freely editable (§7). It never survives into `Accepted` or `Rejected`: §8's third refusal blocks that transition while one is outstanding, because acceptance leaves the body byte-identical and would freeze the unconfirmed claim into a record that gates every subsequent plan.

**No asserted deliberation.** AWS requires Context to mention the solutions the team "considered", and a source listing options is a menu rather than deliberation — a dependency file naming three queue libraries is not evidence anyone weighed three queue libraries. An alternative the user did not name is either asked about or omitted, and never written as considered. Writing one in fabricates a discussion, and the record then closes a question the team never opened.

**No unsourced quantities.** A number in a record traces to the user or to a cited file, or it does not appear at all. An invented "roughly 40% of requests", added to make a Context bullet concrete, becomes the figure a later decision is argued from — and no marker fixes it, because the problem is that the quantity has no source rather than that its source is the agent.
