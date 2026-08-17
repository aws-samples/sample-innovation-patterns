"""Offline tests pinning the secret-redaction filter and the gate scanner.

In the offline tier because they must run without deploying anything — the value being
redacted is the one secret this harness generates, and a test that needed a live
Cognito pool to check the filter would only run on the billable path.
"""

from __future__ import annotations

from pathlib import Path

import cognito_auth
import driver
import standing


# --------------------------------------------------------------------------- #
# The redaction filter
# --------------------------------------------------------------------------- #


def test_the_transcript_writer_redacts_a_registered_secret(tmp_path: Path):
    """Keyed on the LIVE VALUE at the writer, not applied by care at each write site —
    care at each site is what a later-added sink escapes."""
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    secret = "Sup3rS3cret!Value"
    transcript.register_secret(secret)

    transcript.record("assistant_text", text=f"the password is {secret} ok")

    written = transcript.path.read_text()
    assert secret not in written
    assert "***REDACTED***" in written


def test_redaction_covers_a_secret_nested_anywhere_in_the_payload(tmp_path: Path):
    transcript = driver.Transcript(path=tmp_path / "t.jsonl")
    secret = "An0ther!Secret"
    transcript.register_secret(secret)

    transcript.record(
        "ask_user_question",
        questions=[{"question": "q", "note": f"leaked {secret}"}],
        answers={"q": secret},
    )

    assert secret not in transcript.path.read_text()


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
    secret = "P0inter!Secret"
    transcript.register_secret(secret)

    text = standing.render_pointer(
        "itaaa", "dev", "us-east-1", "p", [], {"APP_URL": f"https://x/{secret}"}
    )
    assert secret not in transcript.redact(text)


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
