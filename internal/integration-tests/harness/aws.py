"""How the harness reaches AWS. ONE definition, so no call site can disagree.

Two questions live here that look like one, and conflating them is what made the
previous design look unavoidable:

1.  **How does the harness authenticate?** From botocore's default credential chain,
    naming no profile. See ``session``.
2.  **What profile name does the driven project need in its own ``.env``?** A real
    name, supplied by ``profile_for_env``, and never used to build a session.

Keeping them separate is what lets the harness run unchanged on a workstation and in a
CI container while still satisfying four shipped skills that stop when ``AWS_PROFILE``
is missing from a project's configuration.
"""

from __future__ import annotations

import os

import boto3

# Read ONCE at import, not per call. A call-time read would let two calls in one run
# target different regions, which is precisely the disagreement this module exists to
# make impossible.
REGION = os.environ.get("IPA_IT_REGION", "us-east-1")


def session(region: str = REGION) -> boto3.Session:
    """Region PINNED, credentials from the DEFAULT CHAIN.

    The region is explicit because this shell exports ``AWS_REGION=us-west-2``, and an
    inherited region would probe an account that is clean only because nothing was ever
    there -- a false pass that is indistinguishable from a correct one.

    The credentials are ambient ON PURPOSE. The chain reads the environment or an SSO
    cache on a workstation and the ECS container role inside CodeBuild, so one code
    path serves both and no maintainer's profile name appears in source.
    """
    return boto3.Session(region_name=region)


def cli_region_args(region: str = REGION) -> list[str]:
    """The region flags for an ``aws`` CLI argv. NEVER a ``--profile`` flag.

    Kept despite wrapping two list elements, because it is the grep-able marker that an
    argv site was reviewed during the profile removal. An inline ``["--region", REGION]``
    is indistinguishable from a site that was missed.
    """
    return ["--region", region]


def profile_for_env() -> str:
    """The value the AGENT writes to ``.env``'s ``AWS_PROFILE``. Never builds a session.

    Separate from ``session`` because the two answer different questions. Four shipped
    skills -- ``/ipa-compose``, ``/ipa-prepare``, ``/ipa-security`` and ``/ipa-destroy``
    -- STOP when ``AWS_PROFILE`` is absent from ``.env``, so a driven run needs a name
    there. Nothing in this harness needs one to make an AWS call.

    Raises rather than defaulting to ``"default"``: ``AWS_PROFILE=default`` in ``.env``
    is accepted by ``/ipa-init`` and then fails much later inside a generated Makefile,
    with an error naming a missing profile rather than the configuration step that
    should have supplied one.
    """
    value = os.environ.get("AWS_PROFILE", "").strip()
    if not value:
        raise RuntimeError(
            "AWS_PROFILE is not set. The harness's own AWS calls do not need it, but "
            "/ipa-init writes it to .env and /ipa-compose, /ipa-prepare, /ipa-security "
            "and /ipa-destroy all stop without it. Locally: export AWS_PROFILE=<your "
            "profile>. In CodeBuild it is set to 'ipa-it', a credential-less profile "
            "the install phase creates so the CLI falls through to container "
            "credentials."
        )
    return value
