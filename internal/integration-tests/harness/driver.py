"""Drive the IPA lifecycle skills unattended through one Claude Agent SDK session.

Five traps are designed out here rather than debugged later. Each one produced a
failure whose symptom names nothing relevant:

1. **``env`` REPLACES the child environment**, so it is merged over ``os.environ``.
   A bare three-key dict strands the child without ``PATH`` and without the AWS
   credential chain, and the handshake dies about 66 seconds later with
   ``Control request timeout: initialize`` — which names neither.
2. **The region is PINNED, not inherited.** This shell exports
   ``AWS_REGION=us-west-2``. The generated Makefiles pass ``--region`` explicitly at
   28 sites and so follow ``.env``, but ``/ipa-deploy`` Step 1.5's
   ``describe-stacks`` is a bare ``aws`` call with no ``--region``
   (``ipa-deploy/SKILL.md:127``). Left unpinned, that gate looks in ``us-west-2``,
   finds nothing, and hard-stops with *"Security stack is not deployed"* after Route
   A demonstrably deployed it in ``us-east-1``.
3. **ONE long-lived client for the whole session.** A client per lifecycle stage
   closes its input stream when the stage's prompt is exhausted, after which the
   answer callback can no longer fire — producing a run that stops at the first
   question with no error, no output, and no sign that it is waiting.
4. **The ``PreToolUse`` hook is what answers the questions**, not ``can_use_tool``.
   Measured (reference ``iac_compose/FINDINGS.md`` F2), contradicting both the SDK
   documentation and this repository's own 2026-07-31 research. ``can_use_tool`` is
   registered anyway as a **tripwire**: without it, an SDK that switches channels
   would silently fall through to skill defaults (``APP_NAMESPACE=app``) while
   reporting success. Both paths funnel into the same resolver so they cannot
   disagree.
5. **``setting_sources=["project"]``** is required for the temp project's
   ``.claude/skills/ipa-*`` to load at all.
6. **A finished turn is not a finished lifecycle.** ``ResultMessage(subtype='success',
   stop_reason='end_turn')`` is what the SDK reports for a drive that stopped a tenth
   of the way through ``/ipa-compose`` — measured twice at the same boundary, where
   compose delegates to ``/ipa-security``. Nothing in the result distinguishes that
   from completion, so ``drive`` takes an ``is_complete`` predicate supplied by the
   scenario, checks it against disk and AWS, and nudges a bounded number of times.
   Without it the truncation surfaces twenty-one ``describe_stacks`` failures later,
   naming a missing stack rather than the turn that ended.

``permission_mode="acceptEdits"`` is the only mode where the answer path is both
reachable and un-shadowed: ``dontAsk`` denies ``AskUserQuestion`` without invoking
anything, and ``bypassPermissions`` raises ``CanUseToolShadowedWarning``.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.answers import AnswerResolver

# The SDK is an OPTIONAL extra (`uv sync --all-extras`), so it is imported lazily.
#
# A module-level import here would make `import driver` fail on a machine without the
# extra -- and `conftest.py` imports this module, so pytest could not even COLLECT the
# offline tests. That would defeat the whole point of putting the SDK behind an extra:
# the offline tier is meant to run anywhere, on any checkout, with no credentials and
# no agent. Verified by running the suite on a fresh checkout, where it failed.
#
# Everything in this module that the offline tier touches -- Transcript, the redaction
# filter, scan_for_gates, BILLABLE_GATE_MARKERS, the prompts -- is pure Python and
# stays importable. Only building a session needs the SDK, and that is the billable
# path, which `conftest.py` already gates on the `claude_agent_sdk_importable` probe.
try:  # pragma: no cover - exercised by presence/absence of the extra
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        HookMatcher,
        PermissionResultAllow,
    )

    SDK_AVAILABLE = True
    SDK_IMPORT_ERROR = ""
except ImportError as _exc:  # pragma: no cover
    ClaudeAgentOptions = ClaudeSDKClient = HookMatcher = PermissionResultAllow = None  # type: ignore[assignment,misc]
    SDK_AVAILABLE = False
    SDK_IMPORT_ERROR = str(_exc)


def _require_sdk() -> None:
    """Fail with an actionable message rather than a NameError."""
    if not SDK_AVAILABLE:
        raise RuntimeError(
            f"claude_agent_sdk is not installed ({SDK_IMPORT_ERROR}). It is an "
            "optional extra so the offline tier runs without it. Install with: "
            "uv sync --all-extras"
        )

REGION = os.environ.get("IPA_IT_REGION", "us-east-1")
MODEL = os.environ.get(
    "IPA_IT_DRIVER_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)

#: Phase 3 ceiling (HITL default Q2.A). The reference measured its compose-only path
#: at $1.61-$2.41 over 8-13 minutes; IPA's compose reads more stack skills and adds
#: /ipa-security, so 5 leaves headroom without letting a wedged run spend Phase 4's
#: budget. Phase 4 raises both -- see ``full_lifecycle_options``.
MAX_BUDGET_USD = float(os.environ.get("IPA_IT_MAX_BUDGET_USD", "5"))
MAX_TURNS = int(os.environ.get("IPA_IT_MAX_TURNS", "300"))

#: The FULL-LIFECYCLE ceiling, and a SEPARATE variable from ``IPA_IT_MAX_BUDGET_USD`` on
#: purpose. The two scopes differ roughly threefold, and each scenario sets its own
#: ceiling inline -- so one shared variable set for the compose scenario would cap a
#: deploy run at $5 and stop it partway through a deployment. A drive stopped by a
#: ceiling is indistinguishable from a wedge and leaves partial infrastructure standing,
#: which is the cheap scenario's configuration causing the expensive scenario's worst
#: failure.
#:
#: Previously a literal ``15.0`` inside ``full_lifecycle_options``, which meant the
#: documented spend ceiling could not reach the only path able to exhaust it.
FULL_MAX_BUDGET_USD = float(os.environ.get("IPA_IT_FULL_MAX_BUDGET_USD", "15"))

#: How many times a drive may ask the agent to carry on after it ended its turn with
#: the lifecycle unfinished. See ``drive``'s ``is_complete``.
#:
#: TWO, not more. A nudge is a backstop for a skill that stopped early, and each one
#: re-enters a session that has already demonstrated it thinks it is done. Raising this
#: converts "the skill stops early" into "the harness pays repeatedly to push it
#: through", which hides the defect the counter exists to report. Set to ``0`` to
#: measure the unnudged behaviour of the skills as authored.
MAX_NUDGES = int(os.environ.get("IPA_IT_MAX_NUDGES", "2"))

#: IPA's own prose gates, verified in source. The reference's markers were its own
#: and do not transfer.
#:
#: Matched case-insensitively, and the FULL SURROUNDING TEXT is recorded verbatim.
#: What the agent *said* while crossing a billable boundary is the finding -- whether
#: it asked, assumed, warned, or simply proceeded. A boolean "did it proceed"
#: discards the entire content of the finding.
BILLABLE_GATE_MARKERS = {
    # /ipa-prepare SKILL.md:136
    "prepare:proceed": "proceed? (yes/no)",
    # /ipa-deploy SKILL.md:189
    "deploy:proceed": "proceed with deployment? (yes/no)",
    # /ipa-compose SKILL.md:86 -- re-composition overwrite warning
    "compose:overwrite": "proceed? (yes to overwrite, no to cancel)",
    # /ipa-deploy SKILL.md:226 -- build failure must STOP, not continue
    "deploy:build_failed": "do not proceed to deploy",
    # /ipa-security Step 5
    "security:deploy": "deploy this security configuration?",
}


# --------------------------------------------------------------------------- #
# Transcript
# --------------------------------------------------------------------------- #


@dataclass
class Transcript:
    """Append-only JSONL record, written and flushed PER EVENT.

    Never assembled in memory: on the billable path a hard crash can leave
    infrastructure standing and costing money, and the transcript is then the only
    record of what was created. A record that lives in the crashed process's memory
    is no record at all.
    """

    path: Path
    redactions: list[str] = field(default_factory=list)

    def redact(self, text: str) -> str:
        """Replace every registered secret with a placeholder.

        Keyed on the LIVE VALUE at the writer rather than applied by care at each
        write site -- care at each site is what a later-added sink escapes.
        """
        for secret in self.redactions:
            if secret:
                text = text.replace(secret, "***REDACTED***")
        return text

    def register_secret(self, secret: str) -> None:
        if secret and secret not in self.redactions:
            self.redactions.append(secret)

    def record(self, kind: str, **payload: Any) -> None:
        event = {
            "kind": kind,
            "at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        line = self.redact(json.dumps(event, default=str))
        with self.path.open("a") as fh:
            fh.write(line + "\n")
            fh.flush()

    def record_source(self, source: Any) -> None:
        """First entry: WHAT TREE the run ran against.

        A result that names a passing run but not the tree it ran against is not a
        result, and for a dirty tree the commit alone is a false description.
        """
        self.record(
            "source",
            commit=getattr(source, "commit", None),
            dirty=getattr(source, "dirty", None),
            file_count=getattr(source, "file_count", None),
            root=str(getattr(source, "root", "")),
        )


def scan_for_gates(transcript: Transcript, text: str) -> list[str]:
    """Record every billable-gate marker present in assistant text."""
    lowered = text.lower()
    hit: list[str] = []
    for gate, marker in BILLABLE_GATE_MARKERS.items():
        if marker in lowered:
            # FULL surrounding text, verbatim.
            transcript.record("billable_gate", gate=gate, marker=marker, text=text)
            hit.append(gate)
    return hit


# --------------------------------------------------------------------------- #
# The appended system prompt
# --------------------------------------------------------------------------- #

#: The bound on how far the agent proceeds, held as a NAMED REPLACEABLE BLOCK.
#: Phase 4 SUBSTITUTES this rather than appending a wider authorization beside it:
#: two conflicting directives leave the choice of which to honour outside the
#: harness's control.
STOP_AFTER_COMPOSE = """\
## Scope of this run — STOP AFTER COMPOSE

Run `/ipa-init` and then `/ipa-compose`. When `/ipa-compose` prints its completion
report, STOP and report what was generated.

Do NOT run `/ipa-prepare`, `/ipa-deploy`, or any `make` target from `scripts/`.
Those create billable AWS resources and are out of scope for this run. Delegating to
`/ipa-security` from `/ipa-compose` Step 1.5 IS in scope — it deploys two IAM roles,
which are free.
"""

FULL_LIFECYCLE = """\
## Scope of this run — FULL LIFECYCLE AUTHORIZED

Run the complete IPA lifecycle: `/ipa-init`, `/ipa-compose`, `/ipa-prepare`, then
`/ipa-deploy`. You are authorized to create billable AWS resources.

When a skill asks a plain-text confirmation such as "Proceed? (yes/no):", answer
`yes` and state briefly why you are proceeding. Do not stop to ask the operator:
this run is unattended and nobody is watching the terminal.

Report the deployed URLs when `/ipa-deploy` completes.
"""


def unattended_append(namespace: str, profile: str, scope: str) -> str:
    """The instruction appended to the preset system prompt."""
    return f"""\
# Unattended integration-test run

You are being driven by an automated integration test with no human watching. Never
wait for operator input. Answer every `AskUserQuestion` and every plain-text
confirmation yourself and keep going.

## Pinned configuration — use these values exactly

- **`APP_NAMESPACE` MUST be `{namespace}`.** Do not use `app`, and do not invent one.
  `/ipa-init`'s namespace question offers exactly one option, `"app" (Recommended)`,
  so you must supply `{namespace}` through the question's free-text ("Other") path.
  This value is how the test finds and removes what it created; a different namespace
  strands billable infrastructure under a name nothing looks for.
- **`AWS_PROFILE` MUST be `{profile}`.** Do NOT choose "Skip", which is the
  recommended option: it omits `AWS_PROFILE` from `.env` entirely, and three
  downstream skills require it.
- `AWS_REGION` = `{REGION}`, `APP_ENV` = `dev`, `APP_IAC` = `cloudformation`.

## What to build

A web app with a REST API and a background queue, with Cognito authentication.

## Two rules that prevent unrecoverable mistakes

**1. Never run a `make` target that writes `.env` and one that reads it in the same
invocation.** Make loads `.env` via `-include` ONCE at parse time, so an invocation
cannot see values its own `update-env` step wrote during that same invocation — they
read as empty, and the resulting error looks like a template bug rather than a
sequencing mistake. Always use two separate `make` invocations: one to sync the
environment, then a fresh one to consume it.

**2. Never recompute `CognitoDomainPrefix`. Always read `COGNITO_DOMAIN_PREFIX`
from `.env`.** Recomputing it changes a property on `AWS::Cognito::UserPoolDomain`
that CloudFormation treats as REPLACE, which destroys the live domain. That is not
recoverable within this run and its cause is invisible in the resulting error.

{scope}"""


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


def build_options(
    project: Path,
    resolver: AnswerResolver,
    transcript: Transcript,
    scope: str = STOP_AFTER_COMPOSE,
    max_budget_usd: float | None = None,
    max_turns: int | None = None,
) -> "ClaudeAgentOptions":
    """Assemble the SDK options. See the module docstring for the five traps."""
    _require_sdk()

    def _answer(questions: list[dict[str, Any]], via: str) -> dict[str, str]:
        """Resolve one batch and record which channel delivered it.

        ``UnknownQuestion`` deliberately propagates: aborting with the question text
        beats guessing, because a guess writes a subtly wrong ``.env`` that still
        passes the init gate.
        """
        supplied = resolver.resolve(questions)
        transcript.record(
            "ask_user_question", via=via, questions=questions, answers=supplied
        )
        return supplied

    async def can_use_tool(
        tool_name: str, input_data: dict[str, Any], context: Any
    ) -> PermissionResultAllow:
        """Never fires under acceptEdits. A TRIPWIRE, not redundancy.

        If a future SDK switches channels, this keeps the run from silently falling
        through to skill defaults while reporting success -- and the transcript's
        ``via`` field makes the switch visible as a channel change rather than as a
        wrong namespace three steps later.
        """
        if tool_name != "AskUserQuestion":
            return PermissionResultAllow()
        questions = input_data.get("questions", [])
        return PermissionResultAllow(
            updated_input={
                # questions passed through UNCHANGED; only answers is added.
                "questions": questions,
                "answers": _answer(questions, via="can_use_tool"),
            },
        )

    async def pre_tool_hook(
        input_data: dict[str, Any], tool_use_id: str | None, context: Any
    ) -> dict[str, Any]:
        """Answer AskUserQuestion; pass every other tool through untouched."""
        if input_data.get("tool_name") != "AskUserQuestion":
            return {}
        questions = input_data.get("tool_input", {}).get("questions", [])
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {
                    "questions": questions,
                    "answers": _answer(questions, via="pre_tool_use_hook"),
                },
            }
        }

    return ClaudeAgentOptions(
        cwd=str(project),
        # Required for the temp project's .claude/skills/ipa-* to load at all.
        setting_sources=["project"],
        env={
            **os.environ,
            "CLAUDE_CODE_USE_BEDROCK": "1",
            # PINNED, not inherited. See trap 2 in the module docstring.
            "AWS_REGION": REGION,
            "AWS_DEFAULT_REGION": REGION,
            "ANTHROPIC_MODEL": MODEL,
            "AWS_PROFILE": resolver.profile,
        },
        model=MODEL,
        permission_mode="acceptEdits",
        can_use_tool=can_use_tool,
        # matcher=None and filter inside the hook: the reference's measured-working
        # form. A tool-name matcher adds a second place the filter can be wrong.
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[pre_tool_hook])]},
        max_turns=max_turns if max_turns is not None else MAX_TURNS,
        max_budget_usd=(
            max_budget_usd if max_budget_usd is not None else MAX_BUDGET_USD
        ),
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": unattended_append(resolver.namespace, resolver.profile, scope),
        },
    )


def full_lifecycle_options(*args: Any, **kwargs: Any) -> "ClaudeAgentOptions":
    """The substitution: the wider scope AND the raised ceilings together.

    Both change as one. The compose ceilings are sized for a run that stops early, so
    a full lifecycle reaching them looks identical to a wedge.

    The spend ceiling comes from ``FULL_MAX_BUDGET_USD`` -- its own variable, separate
    from ``IPA_IT_MAX_BUDGET_USD``. The two differ threefold and each scenario sets its
    own inline, so a single shared variable set for the compose scenario would cap a
    deploy run at $5 and stop it mid-deployment.

    ``max_turns`` stays a literal, and the asymmetry is deliberate: a turn ceiling is a
    runaway-loop backstop, and making it configurable invites raising it to get past a
    wedge, which is the behaviour it exists to stop.
    """
    kwargs.setdefault("scope", FULL_LIFECYCLE)
    kwargs.setdefault("max_budget_usd", FULL_MAX_BUDGET_USD)
    kwargs.setdefault("max_turns", 600)
    return build_options(*args, **kwargs)


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


@dataclass
class RunResult:
    """Measured facts about one drive. Never predicted."""

    cost_usd: float | None = None
    turns: int | None = None
    wall_clock_s: float | None = None
    stopped_by_ceiling: bool = False
    gates_seen: list[str] = field(default_factory=list)
    channels_used: set[str] = field(default_factory=set)
    final_text: str = ""
    result_payload: dict[str, Any] = field(default_factory=dict)

    #: How many times ``drive`` had to ask the agent to carry on after it ended its
    #: turn with the lifecycle unfinished. **Zero is the only good value** -- every
    #: nudge is a skill that stopped where it should have continued, and the whole
    #: reason this is a counter rather than a boolean is that it must be reportable.
    nudges: int = 0

    #: What was still missing at the last check, verbatim from ``is_complete``.
    #: Empty means the drive finished complete.
    incomplete_reason: str = ""

    #: EVERY ``ResultMessage`` cost, in order. ``cost_usd`` keeps only the last one,
    #: and a nudged drive produces several -- whether the SDK's figure is cumulative
    #: or per-query is not measured here, so the list is recorded rather than a sum
    #: inferred from an assumption about which it is.
    cost_reports: list[float] = field(default_factory=list)


def _record_message(transcript: Transcript, message: Any, result: RunResult) -> None:
    """Record one SDK message, flattening the parts worth asserting on later."""
    kind = type(message).__name__
    texts: list[str] = []
    for block in getattr(message, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            texts.append(text)
    # NB: the payload key is `msg_kind`, not `kind` -- `record`'s own first parameter
    # is named `kind`, so a `kind=` payload key raises TypeError for multiple values.
    if texts:
        joined = "\n".join(texts)
        transcript.record("assistant_text", msg_kind=kind, text=joined)
        result.gates_seen += scan_for_gates(transcript, joined)
        result.final_text = joined
    else:
        transcript.record("message", msg_kind=kind, repr=repr(message)[:2000])


async def drive(
    prompt: str,
    project: Path,
    resolver: AnswerResolver,
    transcript: Transcript,
    options: "ClaudeAgentOptions | None" = None,
    is_complete: "Callable[[RunResult], tuple[bool, str]] | None" = None,
    max_nudges: int = MAX_NUDGES,
) -> RunResult:
    """Drive one session to completion with ONE long-lived client.

    See trap 3: a client per lifecycle stage closes its input stream before the
    answer callback can fire, producing a silent hang.

    ``is_complete`` is the CALLER's definition of "the lifecycle finished", returning
    ``(done, what_is_missing)``. It exists because ``ResultMessage(subtype='success',
    stop_reason='end_turn')`` is what the SDK reports for a run that stopped a tenth
    of the way through ``/ipa-compose`` -- an agent ending its turn is
    indistinguishable, from here, from an agent finishing the work. Measured twice at
    the same boundary (``/ipa-compose`` Step 1.5 delegating to ``/ipa-security``):
    both runs reported success having generated no artifacts.

    When the predicate says the work is unfinished the drive NUDGES -- sends a
    follow-up on the same client -- up to ``max_nudges`` times. This is deliberately
    a thin backstop and not a fix: each nudge is counted on the result and recorded in
    the transcript, so a run that only completed because it was nudged reports that
    fact rather than looking clean. A ceiling stop is never nudged; spending more on a
    run already stopped for spending is the one case where continuing is certainly
    wrong.
    """
    options = options or build_options(project, resolver, transcript)
    result = RunResult()
    started = time.monotonic()

    transcript.record(
        "run_start",
        namespace=resolver.namespace,
        profile=resolver.profile,
        region=REGION,
        model=MODEL,
        max_budget_usd=options.max_budget_usd,
        max_turns=options.max_turns,
        max_nudges=max_nudges,
        project=str(project),
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            pending = prompt
            while True:
                await client.query(pending)
                async for message in client.receive_response():
                    _record_message(transcript, message, result)
                    if type(message).__name__ == "ResultMessage":
                        result.cost_usd = getattr(message, "total_cost_usd", None)
                        if result.cost_usd is not None:
                            result.cost_reports.append(result.cost_usd)
                        result.turns = getattr(message, "num_turns", None)
                        payload = getattr(message, "__dict__", {})
                        result.result_payload = {
                            k: v for k, v in payload.items() if not k.startswith("_")
                        }
                        subtype = str(getattr(message, "subtype", "") or "")
                        # Distinguish "a ceiling stopped it" from "the agent finished".
                        if "max_turns" in subtype or "budget" in subtype:
                            result.stopped_by_ceiling = True

                done, missing = (
                    (True, "") if is_complete is None else is_complete(result)
                )
                result.incomplete_reason = "" if done else missing
                if done or result.stopped_by_ceiling:
                    break
                if result.nudges >= max_nudges:
                    transcript.record(
                        "nudge_exhausted", after=result.nudges, missing=missing
                    )
                    break
                result.nudges += 1
                transcript.record("nudge", attempt=result.nudges, missing=missing)
                # Printed as well as recorded: on a drive whose only other output is a
                # blank screen, a nudge is the one thing a watching maintainer can act
                # on -- it names a skill that stopped early, while the run continues.
                print(f"\nNUDGE {result.nudges}/{max_nudges}: {missing}")
                pending = NUDGE_PROMPT.format(missing=missing)
    finally:
        result.wall_clock_s = time.monotonic() - started
        transcript.record(
            "run_end",
            cost_usd=result.cost_usd,
            cost_reports=result.cost_reports,
            turns=result.turns,
            wall_clock_s=round(result.wall_clock_s, 1),
            stopped_by_ceiling=result.stopped_by_ceiling,
            nudges=result.nudges,
            incomplete_reason=result.incomplete_reason,
            gates_seen=sorted(set(result.gates_seen)),
        )

    # Which channel actually delivered the answers -- read back from the transcript
    # so it reflects what happened rather than what was registered.
    for line in transcript.path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("kind") == "ask_user_question" and event.get("via"):
            result.channels_used.add(event["via"])

    return result


COMPOSE_PROMPT = (
    "Set up this project with IPA and compose a deployment for: "
    "Web App with REST API and background queue with Cognito authentication. "
    "Run /ipa-init first, then /ipa-compose."
)

FULL_PROMPT = (
    "Set up this project with IPA and deploy: "
    "Web App with REST API and background queue with Cognito authentication. "
    "Run /ipa-init, then /ipa-compose, then /ipa-prepare, then /ipa-deploy."
)

#: Sent when a drive ends its turn with the lifecycle unfinished. States WHAT is
#: missing -- supplied by the scenario's ``is_complete`` -- rather than "continue",
#: because the agent has just reported success and needs the specific gap, not
#: encouragement. It deliberately does not name a skill: which step is unfinished is
#: the agent's to work out from the state on disk, and telling it to re-run a named
#: skill is how a nudge turns into a second composition over a half-composed project.
NUDGE_PROMPT = (
    "You ended your turn but the lifecycle is not finished: {missing}\n\n"
    "Nothing has gone wrong and nobody is waiting -- this run is unattended. Check "
    "what is actually on disk and in AWS, work out which step you stopped in the "
    "middle of, and carry on from there through to the end of the lifecycle you were "
    "asked for. Do not start over and do not re-run a step that already completed."
)
