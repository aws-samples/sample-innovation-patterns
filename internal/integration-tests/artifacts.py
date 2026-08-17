"""Parsers for the ``scripts/*.mk`` artifacts ``/ipa-compose`` generates.

Kept as its own module rather than folded into ``test_compose.py``, which has the
only consumer. Separation is what makes the composition assertions testable
offline against fixture Makefiles — which is the whole point of the offline tier.
Folding it in would save one file and lose one test tier.

Every function here reads text and returns data. None of them asserts, so the same
parser serves an offline fixture test and a live composition assertion.
"""

from __future__ import annotations

import re
from pathlib import Path

#: The eight artifacts /ipa-compose reports generating (ipa-compose/SKILL.md:266-274).
#: The claim that all eight appear on a real run had never been observed before
#: this harness; asserting presence is what turns it into a verified fact.
EXPECTED_ARTIFACTS = (
    "scripts/prepare.mk",
    "scripts/deploy.mk",
    "scripts/build.mk",
    "scripts/post-deploy.mk",
    "scripts/env.mk",
    "scripts/test.mk",
    "scripts/release.mk",
    "scripts/SECURITY-DISPOSITION.md",
)


def missing_artifacts(project: Path) -> list[str]:
    """Which of the eight expected artifacts are absent."""
    return [rel for rel in EXPECTED_ARTIFACTS if not (project / rel).exists()]


def read(project: Path, rel: str) -> str:
    return (project / rel).read_text()


# --------------------------------------------------------------------------- #
# Targets and prerequisites
# --------------------------------------------------------------------------- #

#: A target line: name, colon, optional prerequisites. Excludes `::`, pattern
#: rules, and variable assignments (`FOO := bar` has no colon-space form that
#: matches, but `FOO:=bar` would, so `=` is excluded explicitly).
_TARGET_RE = re.compile(r"^([A-Za-z0-9_.\-/]+)\s*:(?!=)\s*(.*)$")


def targets(text: str) -> list[str]:
    """Every target name declared in a Makefile, in declaration order."""
    found: list[str] = []
    for line in text.splitlines():
        if line.startswith("\t"):
            continue
        m = _TARGET_RE.match(line)
        if m and m.group(1) != ".PHONY":
            found.append(m.group(1))
    return found


def target_count(text: str, name: str) -> int:
    """How many times ``name`` is declared as a target.

    A duplicated container-build target either builds twice or builds the wrong
    one depending on ordering, so the count matters and not merely presence.
    """
    return sum(1 for t in targets(text) if t == name)


def prerequisites(text: str, name: str) -> list[str]:
    """The prerequisites of target ``name``, in order.

    Returns an empty list when the target is absent, so a caller distinguishes
    "no prerequisites" from "no target" by checking ``name in targets(text)``.
    """
    for line in text.splitlines():
        if line.startswith("\t"):
            continue
        m = _TARGET_RE.match(line)
        if m and m.group(1) == name:
            return m.group(2).split()
    return []


def target_body(text: str, name: str) -> str:
    """The recipe lines of target ``name``, joined.

    Recipe lines are the tab-indented lines following the target line, up to the
    next non-indented non-blank line.
    """
    lines = text.splitlines()
    body: list[str] = []
    capturing = False
    for line in lines:
        if not line.startswith("\t"):
            m = _TARGET_RE.match(line)
            if m and m.group(1) == name:
                capturing = True
                continue
            if capturing and line.strip():
                break
            continue
        if capturing:
            body.append(line)
    return "\n".join(body)


def _suffixes(prereqs: list[str], prefix: str) -> list[str]:
    """Strip a ``deploy-``/``teardown-`` prefix, leaving the tier suffixes."""
    return [p[len(prefix) :] if p.startswith(prefix) else p for p in prereqs]


def teardown_is_reverse_of_deploy(text: str) -> tuple[bool, list[str], list[str]]:
    """Whether ``teardown:``'s prerequisites are the exact reverse of ``deploy:``'s.

    Compares TIER SUFFIXES, not raw target names. ``MAKEFILE_TEMPLATES.md:54``
    generates ``deploy: deploy-{suffix1} ... deploy-{suffixN}`` and ``:162``
    generates ``teardown: teardown-{suffixN} ... teardown-{suffix1}`` — so the two
    prerequisite lists never share a name, and comparing them raw reports every
    healthy artifact as misordered.

    Teardown in any order other than the exact reverse fails on a resource another
    still depends on, and the failure leaves a partially removed deployment — more
    expensive to reason about than either a complete one or none.

    Returns ``(ok, deploy_prereqs, teardown_prereqs)`` so a failing assertion can
    show both lists rather than only a boolean.
    """
    dep = prerequisites(text, "deploy")
    tear = prerequisites(text, "teardown")
    ok = bool(dep) and bool(tear) and _suffixes(tear, "teardown-") == list(
        reversed(_suffixes(dep, "deploy-"))
    )
    return ok, dep, tear


# --------------------------------------------------------------------------- #
# Parameter overrides
# --------------------------------------------------------------------------- #

_PARAM_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s\\]+)")


def parameter_overrides(text: str, target: str) -> dict[str, str]:
    """The ``Key=Value`` pairs a target passes as CloudFormation parameter overrides.

    Used for the one artifact-level proof that compose's cross-tier auto-wiring
    fired: ``deploy-backend`` must carry ``EnableSqsIntegration=true``. Without it
    the tiers deploy independently and the failure appears only at runtime, as a
    job accepted and never processed.
    """
    body = target_body(text, target)
    if "--parameter-overrides" not in body:
        return {}
    after = body.split("--parameter-overrides", 1)[1]
    return dict(_PARAM_RE.findall(after))


# --------------------------------------------------------------------------- #
# The deploy.mk header tier set
# --------------------------------------------------------------------------- #

_HEADER_TIER_RE = re.compile(r"^#.*\b(?:stacks?|tiers?)\b\s*:\s*(.+)$", re.IGNORECASE)


def header_tiers(text: str) -> set[str]:
    """The tier set recorded in a generated Makefile's header comment.

    ``/ipa-compose`` Step 0.3a reads this back on an idempotent refresh, so it is
    the artifact's own record of what was composed. A composition that silently
    omits a tier generates artifacts that succeed at everything they attempt while
    deploying a different architecture than the one asked for.

    Falls back to deriving the set from ``deploy-*`` target names when no header
    line is present, so a header-format change degrades to a weaker check rather
    than to a false pass.
    """
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        m = _HEADER_TIER_RE.match(line)
        if m:
            raw = m.group(1).replace(",", " ")
            return {t.strip() for t in raw.split() if t.strip()}
    return {
        t[len("deploy-") :]
        for t in targets(text)
        if t.startswith("deploy-") and t != "deploy-all"
    }
