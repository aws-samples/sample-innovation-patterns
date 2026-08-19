"""Pinned answers for the questions IPA's lifecycle skills ask, and the run namespace.

Two behaviours here are load-bearing, and both are about failing loudly:

*   **``resolve()`` RAISES on an unknown question.** ``/ipa-init`` batches its five
    questions into two ``AskUserQuestion`` calls, four then one (``SKILL.md:111``).
    Answering three and guessing the fourth writes an ``.env`` that is wrong in one
    field and still passes the init gate — so the run continues and fails later,
    somewhere that does not mention the field. Raising converts that into an
    immediate, named failure.

    The four-then-one split is the tool's limit, not a preference, and it is why
    this table is keyed per question rather than per batch: ``resolve()`` is called
    once per call, and neither call is "the init batch". Until 2026-08-18 the skill
    asked all five at once with a one-option namespace question, which
    ``AskUserQuestion`` rejects outright — so the hook never fired, this whole table
    went unused, and the agent wrote ``.env`` from the appended system prompt
    instead. Nothing in the compose scenario's assertions distinguished that from a
    working answer path except ``test_the_answer_channel_is_recorded``.
*   **``make_namespace()`` asserts at the point of generation.** An invalid
    namespace is otherwise accepted by everything until a deployment rejects it,
    many minutes later, with a Cognito domain-prefix error that never mentions the
    namespace.

Question text is the primary key so that a prose edit to a skill surfaces as a
failure rather than as a silently different answer. The option-label-set fallback
exists for a reworded question whose options are unchanged.
"""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass, field

from harness import aws

# --------------------------------------------------------------------------- #
# Namespace rules — THE single definition. Nothing else may restate these.
# --------------------------------------------------------------------------- #

#: From /ipa-init's own validation table (SKILL.md:85): 1-12 chars, lowercase
#: letters/digits/hyphens, must start with a letter.
NS_PATTERN = r"^[a-z][a-z0-9-]{0,11}$"
NS_RE = re.compile(NS_PATTERN)

#: Cognito rejects these substrings in a hosted-UI domain prefix. Recorded in
#: infra/cfn/cognito/cognito.yml's own comment on the CognitoDomainPrefix
#: parameter, and the namespace flows into that prefix.
NS_FORBIDDEN = ("cognito", "aws", "amazon")

NS_MAX_LEN = 12


def make_namespace(injected: str | None = None) -> str:
    """Return a validated run namespace.

    Validation happens INSIDE this function so an injected namespace and a
    generated one pass through the same gate. That is what Phase 5's
    ``IPA_IT_NAMESPACE`` seam depends on: a caller writing
    ``namespace or make_namespace()`` would otherwise never check the injected
    value at all.

    Raises ``ValueError`` naming the specific rule violated, never a generic
    message.

    ``None`` means "generate one". An **empty string is invalid, not absent** —
    otherwise ``make_namespace("")`` would silently generate a namespace, and a
    caller that meant to inject one would get a different namespace than it
    recorded. Callers reading an environment variable must therefore pass
    ``os.environ.get(...) or None``.
    """
    ns = "it" + secrets.token_hex(5) if injected is None else injected

    if not ns:
        raise ValueError("namespace is empty")
    if len(ns) > NS_MAX_LEN:
        raise ValueError(
            f"namespace {ns!r} is {len(ns)} chars; max is {NS_MAX_LEN}"
        )
    if ns.startswith("-"):
        raise ValueError(f"namespace {ns!r} must not start with a hyphen")
    if ns.endswith("-"):
        raise ValueError(f"namespace {ns!r} must not end with a hyphen")
    if "--" in ns:
        raise ValueError(f"namespace {ns!r} must not contain consecutive hyphens")
    if not NS_RE.match(ns):
        raise ValueError(f"namespace {ns!r} violates {NS_PATTERN}")
    for bad in NS_FORBIDDEN:
        if bad in ns:
            raise ValueError(
                f"namespace {ns!r} contains {bad!r}, which Cognito forbids in a "
                "hosted-UI domain prefix"
            )
    return ns


# --------------------------------------------------------------------------- #
# The answer table
# --------------------------------------------------------------------------- #

#: HITL default K1.A. Matches Phase 1's probe, and satisfies /ipa-deploy Step 1.5
#: identically to PowerUserAccess: that gate checks stack status only and never
#: assumes either role.
MANAGED_POLICY_ANSWER = "ReadOnlyAccess"

#: Sentinel marking an answer whose value is computed per run rather than fixed.
_NAMESPACE = "<namespace>"
_PROFILE = "<profile>"


@dataclass(frozen=True)
class Answer:
    """One pinned answer.

    ``free_text`` records that the value is typed into the question's built-in
    "Other" path rather than selected from an offered option. It exists so the
    resolver never returns the literal placeholder label: returning ``"Other"``
    writes the word "Other" into ``.env``, and it is accepted.
    """

    value: str
    free_text: bool = False
    options: tuple[str, ...] = field(default=())
    note: str = ""


#: Nine entries, keyed by EXACT question text as the skills state it.
#:
#: The five ``/ipa-init`` entries arrive across TWO calls (four questions, then one),
#: so the resolver sees two batches. Nothing here depends on which batch a question
#: came in — deliberately, because the split is the tool's 4-per-call limit and
#: regrouping the questions must not require touching this table.
#:
#: Questions 6 and 7 are held separately on purpose. /ipa-compose asks "How should
#: IPA configure security infrastructure?" offering "Managed Policy ARN";
#: /ipa-security asks "How should IPA configure IAM execution roles?" offering
#: "Managed policy". They occupy the same role and differ in wording, so a future
#: prose edit aligning them must not collapse them into one entry — one skill
#: would then silently receive the other's answer.
ANSWERS: dict[str, Answer] = {
    # --- /ipa-init, five questions across TWO calls: 1-4, then 5 (SKILL.md:111) -
    "Which AWS CLI profile should IPA use?": Answer(
        value=_PROFILE,
        free_text=True,
        options=("Skip", "default"),
        note=(
            "Answered with a REAL profile name via the built-in Other path. "
            "'Skip' (the recommended option) omits AWS_PROFILE from .env "
            "entirely, and three downstream skills require it — so accepting the "
            "recommendation here would fail later."
        ),
    ),
    "Which AWS region for deployments?": Answer(
        value="us-east-1",
        options=("us-east-1", "us-west-2", "eu-west-1"),
        note=(
            "Itself the recommended option, so agreement on it cannot prove the "
            "harness answered. The namespace is the only discriminator."
        ),
    ),
    (
        "Choose a project namespace. All CloudFormation stacks start with "
        "`{namespace}-{env}-`. Must be unique per account+environment. "
        "(1-12 chars, lowercase letters/digits/hyphens, starts with letter)"
    ): Answer(
        value=_NAMESPACE,
        free_text=True,
        options=("app", "sandbox"),
        note=(
            "The ONLY discriminator between 'the harness answered' and 'the agent "
            "used skill defaults'. Neither offered option is ever the answer -- the "
            "run namespace goes through the built-in Other path -- and the driver "
            "ALSO states it in the appended system prompt, because a single channel "
            "for the one value that proves interception is thin. "
            "'sandbox' is the second option because a one-option question is "
            "REJECTED by AskUserQuestion, which is how this question silently "
            "disabled the whole answer path until 2026-08-18."
        ),
    ),
    "Which environment?": Answer(
        value="dev",
        options=("dev", "stage", "prod"),
    ),
    "Which infrastructure-as-code tool?": Answer(
        value="cloudformation",
        options=("cloudformation", "terraform"),
        note=(
            "Pinned. An unbounded Terraform provider range with no committed "
            "lockfile makes a green run and a red run differ by an upstream "
            "release."
        ),
    ),
    # --- /ipa-compose Step 1.5 (SKILL.md:122) ---------------------------------
    "How should IPA configure security infrastructure?": Answer(
        value="Managed Policy ARN",
        options=(
            "Existing Role ARN",
            "Managed Policy ARN",
            "Innovation Builder Stack",
        ),
        note=(
            "Route A. Delegates to /ipa-security so a REAL {ns}-{env}-security "
            "stack exists — which /ipa-deploy Step 1.5 requires and which "
            "/ipa-compose Step 1.5 does not."
        ),
    ),
    # --- /ipa-security (SKILL.md:107) -----------------------------------------
    "How should IPA configure IAM execution roles?": Answer(
        value="Managed policy",
        options=(
            "Innovation Builder Stack",
            "Managed policy",
            "Existing role ARNs",
        ),
        note="Distinct entry from /ipa-compose's question. Do not merge.",
    ),
    "Which managed policy should IPA attach to both execution roles?": Answer(
        value=MANAGED_POLICY_ANSWER,
        options=("PowerUserAccess", "ReadOnlyAccess"),
        note="HITL default K1.A: ReadOnlyAccess over the recommended PowerUserAccess.",
    ),
    "Deploy this security configuration?": Answer(
        value="Yes, deploy",
        options=("Yes, deploy", "No, start over"),
    ),
}

assert len(ANSWERS) == 9, f"expected nine pinned answers, found {len(ANSWERS)}"


class UnknownQuestion(RuntimeError):
    """Raised when the resolver is asked something it has no pinned answer for.

    Deliberately fatal. A partial map is the failure mode this whole module is
    built to prevent.
    """


class AnswerResolver:
    """Resolves a batch of questions into pinned answers, or raises."""

    def __init__(self, namespace: str, profile: str) -> None:
        # Passed THROUGH make_namespace, not around it, so an injected value is
        # validated by the same gate a generated one is.
        self.namespace = make_namespace(namespace)
        self.profile = profile

    # -- lookup ------------------------------------------------------------- #

    def _by_text(self, text: str) -> Answer | None:
        # Exact text first, then whitespace-normalised, so a rewrapped prompt
        # still matches its own entry.
        if text in ANSWERS:
            return ANSWERS[text]
        norm = " ".join(text.split())
        for question, answer in ANSWERS.items():
            if " ".join(question.split()) == norm:
                return answer
        return None

    def _by_options(self, labels: list[str]) -> Answer | None:
        """Fallback: match on the SET of offered option labels.

        Consulted only when exact-text lookup misses, so a reworded question with
        unchanged options still resolves. Labels are compared with any
        "(Recommended)" suffix stripped, because that decoration is presentational.
        """
        offered = {self._strip_recommended(label) for label in labels}
        if not offered:
            return None
        for answer in ANSWERS.values():
            if answer.options and offered == set(answer.options):
                return answer
        return None

    @staticmethod
    def _strip_recommended(label: str) -> str:
        return label.replace("(Recommended)", "").strip()

    def _materialise(self, answer: Answer) -> str:
        """Substitute the per-run sentinels.

        A free-text answer's value is the TEXT ITSELF, never the literal
        placeholder label the tool uses to offer the free-text path.
        """
        if answer.value == _NAMESPACE:
            return self.namespace
        if answer.value == _PROFILE:
            return self.profile
        return answer.value

    # -- public API --------------------------------------------------------- #

    def resolve_one(self, text: str, labels: list[str] | None = None) -> str:
        answer = self._by_text(text)
        if answer is None:
            answer = self._by_options(labels or [])
        if answer is None:
            raise UnknownQuestion(
                f"no pinned answer for question {text!r} "
                f"(offered options: {labels!r}). Refusing to guess: answering some "
                "questions in a batch and guessing one writes a subtly wrong .env "
                "that still passes the init gate."
            )
        return self._materialise(answer)

    def resolve(self, questions: list[dict]) -> dict[str, str]:
        """Resolve a whole batch, or raise if ANY question is unknown.

        Raises before returning anything, so a batch containing one unknown
        question yields no partial map.
        """
        resolved: dict[str, str] = {}
        for q in questions:
            text = q.get("question") or q.get("text") or ""
            labels = [
                o.get("label", "") if isinstance(o, dict) else str(o)
                for o in (q.get("options") or [])
            ]
            resolved[text] = self.resolve_one(text, labels)
        return resolved


def resolver_from_env(profile: str | None = None) -> AnswerResolver:
    """Build a resolver, honouring the ``IPA_IT_NAMESPACE`` seam.

    The injected namespace is passed through ``make_namespace`` inside
    ``AnswerResolver.__init__``, which is what validates it.

    The profile comes from ``AWS_PROFILE`` alone and RAISES when unset. There is
    deliberately no ``"default"`` fallback: that value is accepted by ``/ipa-init``,
    written into ``.env``, and then fails much later inside a generated Makefile with
    an error naming a missing profile rather than the configuration step that should
    have supplied one. The resolver still needs a real profile STRING because the
    answer table has a profile question to answer -- what changed is that nothing
    authenticates with it.
    """
    injected = os.environ.get("IPA_IT_NAMESPACE") or None
    resolved_profile = profile or aws.profile_for_env()
    return AnswerResolver(
        namespace=injected or make_namespace(), profile=resolved_profile
    )
