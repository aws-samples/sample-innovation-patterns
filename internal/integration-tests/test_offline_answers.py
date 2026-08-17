"""Offline tests for the answer resolver and namespace generation."""

from __future__ import annotations

import pytest

import answers
from answers import AnswerResolver, UnknownQuestion, make_namespace

NAMESPACE_QUESTION = (
    "Choose a project namespace. All CloudFormation stacks start with "
    "`{namespace}-{env}-`. Must be unique per account+environment. "
    "(1-12 chars, lowercase letters/digits/hyphens, starts with letter)"
)


@pytest.fixture
def resolver() -> AnswerResolver:
    return AnswerResolver(namespace="itcafe01", profile="my-profile")


# --------------------------------------------------------------------------- #
# The resolver refuses rather than guesses
# --------------------------------------------------------------------------- #


def test_unknown_question_raises(resolver: AnswerResolver):
    """/ipa-init batches five questions. Guessing one writes a subtly wrong .env
    that still passes the init gate, so the run continues and fails somewhere that
    does not mention the field."""
    with pytest.raises(UnknownQuestion, match="no pinned answer"):
        resolver.resolve_one("What is your favourite colour?", ["blue", "red"])


def test_unknown_question_names_the_question(resolver: AnswerResolver):
    with pytest.raises(UnknownQuestion, match="favourite colour"):
        resolver.resolve_one("What is your favourite colour?", [])


def test_a_batch_with_one_unknown_question_yields_no_partial_map(
    resolver: AnswerResolver,
):
    batch = [
        {"question": "Which environment?", "options": [{"label": "dev"}]},
        {"question": "Totally unknown?", "options": [{"label": "x"}]},
    ]
    with pytest.raises(UnknownQuestion):
        resolver.resolve(batch)


def test_a_fully_known_batch_resolves_every_question(resolver: AnswerResolver):
    batch = [
        {"question": "Which AWS region for deployments?", "options": []},
        {"question": "Which environment?", "options": []},
        {"question": "Which infrastructure-as-code tool?", "options": []},
    ]
    resolved = resolver.resolve(batch)
    assert resolved["Which AWS region for deployments?"] == "us-east-1"
    assert resolved["Which environment?"] == "dev"
    assert resolved["Which infrastructure-as-code tool?"] == "cloudformation"


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #


def test_exact_text_wins_over_the_option_fallback(resolver: AnswerResolver):
    """Exact text is consulted first, so a prose edit surfaces as a failure rather
    than as a silently different answer."""
    got = resolver.resolve_one(
        "Which environment?", ["cloudformation", "terraform"]
    )
    assert got == "dev"


def test_option_set_fallback_resolves_a_reworded_question(resolver: AnswerResolver):
    got = resolver.resolve_one(
        "Which IaC engine would you like?", ["cloudformation", "terraform"]
    )
    assert got == "cloudformation"


def test_recommended_suffix_is_stripped_when_matching_options(resolver: AnswerResolver):
    got = resolver.resolve_one(
        "Reworded region question?",
        ["us-east-1 (Recommended)", "us-west-2", "eu-west-1"],
    )
    assert got == "us-east-1"


def test_the_two_managed_policy_questions_stay_separate_entries():
    """/ipa-compose says 'Managed Policy ARN'; /ipa-security says 'Managed policy'.

    They occupy the same role and differ only in wording. A future prose edit
    aligning them must not collapse them, or one skill silently receives the
    other's answer.
    """
    compose_q = "How should IPA configure security infrastructure?"
    security_q = "How should IPA configure IAM execution roles?"

    assert compose_q in answers.ANSWERS
    assert security_q in answers.ANSWERS
    assert answers.ANSWERS[compose_q] is not answers.ANSWERS[security_q]
    assert answers.ANSWERS[compose_q].value == "Managed Policy ARN"
    assert answers.ANSWERS[security_q].value == "Managed policy"


def test_there_are_exactly_nine_pinned_answers():
    assert len(answers.ANSWERS) == 9


# --------------------------------------------------------------------------- #
# Free text carries the text, never the placeholder
# --------------------------------------------------------------------------- #


def test_namespace_answer_is_the_generated_value_not_the_placeholder(
    resolver: AnswerResolver,
):
    got = resolver.resolve_one(NAMESPACE_QUESTION, ["app (Recommended)"])
    assert got == "itcafe01"
    assert got != "Other"
    assert got != "app"


def test_profile_answer_is_a_real_profile_name_not_skip(resolver: AnswerResolver):
    """'Skip' is the RECOMMENDED option and omits AWS_PROFILE from .env entirely,
    while three downstream skills require it."""
    got = resolver.resolve_one(
        "Which AWS CLI profile should IPA use?", ["Skip (Recommended)", "default"]
    )
    assert got == "my-profile"
    assert got not in ("Skip", "Other")


def test_managed_policy_answer_is_readonlyaccess(resolver: AnswerResolver):
    """HITL default K1.A, matching Phase 1's probe constant."""
    got = resolver.resolve_one(
        "Which managed policy should IPA attach to both execution roles?",
        ["PowerUserAccess (Recommended)", "ReadOnlyAccess"],
    )
    assert got == "ReadOnlyAccess"
    assert got == answers.MANAGED_POLICY_ANSWER


# --------------------------------------------------------------------------- #
# Namespace rules, asserted at the point of generation
# --------------------------------------------------------------------------- #


def test_a_generated_namespace_satisfies_every_rule():
    for _ in range(50):
        ns = make_namespace()
        assert answers.NS_RE.match(ns)
        assert not ns.startswith("-") and not ns.endswith("-") and "--" not in ns
        assert not any(bad in ns for bad in answers.NS_FORBIDDEN)


#: Ten malformed values, each failing at its source. An invalid namespace otherwise
#: surfaces one deployment later as a Cognito domain-prefix error that never
#: mentions the namespace.
MALFORMED = [
    ("thirteenchars", "max is 12"),
    ("", "empty"),
    ("1leading", r"violates"),
    ("-leading", "must not start with a hyphen"),
    ("trailing-", "must not end with a hyphen"),
    ("has--double", "consecutive hyphens"),
    ("HasUpper", "violates"),
    ("has_under", "violates"),
    ("mycognito", "cognito"),
    ("myaws", "aws"),
    ("amazonrun", "amazon"),
]


@pytest.mark.parametrize("value,expected", MALFORMED)
def test_malformed_namespace_fails_at_generation(value: str, expected: str):
    with pytest.raises(ValueError, match=expected):
        make_namespace(value)


def test_there_are_at_least_ten_malformed_cases():
    assert len(MALFORMED) >= 10


def test_an_injected_namespace_is_validated_by_the_resolver():
    """The resolver passes an injected value THROUGH make_namespace, not around it.

    ``namespace or make_namespace()`` would never check an injected value, and a
    malformed one fails much later as a domain-prefix error naming nothing relevant.
    """
    with pytest.raises(ValueError, match="cognito"):
        AnswerResolver(namespace="mycognito", profile="p")


def test_a_valid_injected_namespace_reaches_the_resolver():
    r = AnswerResolver(namespace="itbeef99", profile="p")
    assert r.namespace == "itbeef99"
    assert r.resolve_one(NAMESPACE_QUESTION, ["app"]) == "itbeef99"


# --------------------------------------------------------------------------- #
# The rules have ONE home
# --------------------------------------------------------------------------- #


def test_namespace_rules_are_imported_from_answers_not_restated():
    """A restated rule drifts invisibly in the direction that matters: a test
    carrying its own copy of the pattern passes against that copy while the
    generator uses another.

    Scoped to the harness's own modules -- it cannot detect a copy in code it does
    not inspect, which is why it is named for what it covers.
    """
    import re as _re
    from pathlib import Path as _Path

    here = _Path(__file__).resolve().parent
    # The literal pattern and the forbidden-substring tuple may appear ONLY in
    # answers.py.
    offenders: list[str] = []
    for py in sorted(here.glob("*.py")):
        if py.name == "answers.py":
            continue
        text = py.read_text()
        if _re.search(r"\[a-z\]\[a-z0-9-\]\{0,11\}", text):
            offenders.append(f"{py.name}: restates NS_PATTERN")
        if _re.search(r"[\"']cognito[\"']\s*,\s*[\"']aws[\"']", text):
            offenders.append(f"{py.name}: restates NS_FORBIDDEN")
    assert not offenders, offenders
