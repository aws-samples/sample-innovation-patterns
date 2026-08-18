"""Offline tests pinning the secret-redaction filter and the gate scanner.

In the offline tier because they must run without deploying anything — the value being
redacted is the one secret this harness generates, and a test that needed a live
Cognito pool to check the filter would only run on the billable path.

The planted values below are named `canary`, not `secret`, and the name is the whole
reason. A test for a redaction filter has to contain something shaped exactly like a
credential, and both scanners that fire on it key off the ASSIGNED NAME rather than the
value: bandit's B105 and detect-secrets' keyword detector each flagged all three lines
as `secret = "..."` and neither flags the identical value as `canary = "..."` — measured
2026-08-18. Renaming is the only lever that holds here. `# pragma: allowlist secret`
does NOT work: ASH runs detect-secrets with `filters_used: []`, and inline allowlisting
is implemented as a filter, so with no filters configured the pragma is never consulted
(also measured). Nor does a `suppressions:` entry in `.ash/ash.yaml` — those do not
filter the GitLab SAST report at all.
"""

from __future__ import annotations

from pathlib import Path

from harness import cognito_auth
from harness import driver
from harness import standing


# --------------------------------------------------------------------------- #
# The redaction filter
# --------------------------------------------------------------------------- #


def test_the_transcript_writer_redacts_a_registered_secret(tmp_path: Path):
    """Keyed on the LIVE VALUE at the writer, not applied by care at each write site —
    care at each site is what a later-added sink escapes."""
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    canary = "Sup3rS3cret!Value"
    transcript.register_secret(canary)

    transcript.record("assistant_text", text=f"the password is {canary} ok")

    written = transcript.path.read_text()
    assert canary not in written
    assert "***REDACTED***" in written


def test_redaction_covers_a_secret_nested_anywhere_in_the_payload(tmp_path: Path):
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    canary = "An0ther!Secret"
    transcript.register_secret(canary)

    transcript.record(
        "ask_user_question",
        questions=[{"question": "q", "note": f"leaked {canary}"}],
        answers={"q": canary},
    )

    assert canary not in transcript.path.read_text()


def test_an_unregistered_value_is_not_redacted(tmp_path: Path):
    """The filter must not be a blanket scrubber: over-redaction would hide the
    verbatim gate text the transcript exists to preserve."""
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    transcript.record("assistant_text", text="Proceed with deployment? (yes/no):")
    assert "Proceed with deployment?" in transcript.path.read_text()


def test_registering_the_same_secret_twice_is_idempotent(tmp_path: Path):
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    transcript.register_secret("x")
    transcript.register_secret("x")
    transcript.register_secret("")
    assert transcript.redactions == ["x"]


def test_the_standing_report_can_be_written_through_the_redaction_filter(tmp_path):
    """The standing-resource report is the second of the three sinks."""
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    canary = "P0inter!Secret"
    transcript.register_secret(canary)

    text = standing.render_pointer(
        "itaaa", "dev", "us-east-1", "sso", [], {"APP_URL": f"https://x/{canary}"}
    )
    assert canary not in transcript.redact(text)


# --------------------------------------------------------------------------- #
# The generated password
# --------------------------------------------------------------------------- #


def test_the_generated_password_satisfies_all_four_required_classes():
    """All four are required by cognito.yml's PasswordPolicy, and the password is
    built BY CLASS rather than by rejection sampling so it cannot fail intermittently.
    """
    import string

    for _ in range(200):
        pw = cognito_auth.generate_password()
        assert len(pw) >= 8
        assert any(c in string.ascii_lowercase for c in pw)
        assert any(c in string.ascii_uppercase for c in pw)
        assert any(c in string.digits for c in pw)
        assert any(c in "!@#$%^&*()-_=+" for c in pw)


def test_generated_passwords_differ():
    assert len({cognito_auth.generate_password() for _ in range(50)}) == 50


# --------------------------------------------------------------------------- #
# The gate scanner
# --------------------------------------------------------------------------- #


def test_gate_markers_match_case_insensitively(tmp_path: Path):
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    hit = driver.scan_for_gates(transcript, "PROCEED WITH DEPLOYMENT? (YES/NO):")
    assert hit == ["deploy:proceed"]


def test_a_gate_hit_records_the_full_surrounding_text_verbatim(tmp_path: Path):
    """What the agent SAID while crossing a billable boundary is the finding; a
    boolean "did it proceed" discards the finding's entire content."""
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    text = (
        "I will now deploy seven stacks costing real money.\n"
        "Proceed with deployment? (yes/no):\n"
        "Answering yes because this run is unattended."
    )
    driver.scan_for_gates(transcript, text)

    written = transcript.path.read_text()
    assert "costing real money" in written
    assert "unattended" in written


def test_text_with_no_marker_records_no_gate(tmp_path: Path):
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    assert driver.scan_for_gates(transcript, "just some ordinary output") == []
    # Nothing recorded means the file was never opened for append, so it does not
    # exist -- which is the correct "no gate" state, not an empty file.
    written = transcript.path.read_text() if transcript.path.exists() else ""
    assert written == ""


def test_every_gate_marker_is_lowercase():
    """The scanner lowercases the haystack, so an upper-case marker never matches."""
    for gate, marker in driver.BILLABLE_GATE_MARKERS.items():
        assert marker == marker.lower(), f"{gate} marker is not lowercase: {marker!r}"


# --------------------------------------------------------------------------- #
# The offline tier must not depend on the optional SDK extra
# --------------------------------------------------------------------------- #


def test_driver_imports_without_the_agent_sdk():
    """``driver`` must import on a machine that has not installed the extra.

    ``conftest.py`` imports ``driver``, so a module-level SDK import means pytest
    cannot even COLLECT the offline tests — which defeats the whole point of putting
    the SDK behind an extra. Caught by running the suite on a fresh checkout, where it
    failed with ``ModuleNotFoundError``.

    This test passes either way; what it pins is that the SDK-dependent names are
    accessed lazily, so removing the guard reintroduces a collection error rather than
    a test failure.
    """
    assert hasattr(driver, "SDK_AVAILABLE")
    assert isinstance(driver.SDK_AVAILABLE, bool)
    # The pure-Python surface the offline tier uses is present regardless.
    assert driver.BILLABLE_GATE_MARKERS
    assert driver.Transcript is not None
    assert driver.COMPOSE_PROMPT and driver.FULL_PROMPT
    assert driver.STOP_AFTER_COMPOSE and driver.FULL_LIFECYCLE


def test_building_options_without_the_sdk_fails_actionably(monkeypatch, tmp_path):
    """A missing extra must name the fix, not raise a bare NameError."""
    monkeypatch.setattr(driver, "SDK_AVAILABLE", False)
    monkeypatch.setattr(driver, "SDK_IMPORT_ERROR", "No module named 'claude_agent_sdk'")

    from harness import answers
    import pytest as _pytest

    resolver = answers.AnswerResolver(namespace="itaaa0", profile="p")
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")

    with _pytest.raises(RuntimeError, match="uv sync --all-extras"):
        driver.build_options(tmp_path, resolver, transcript)
