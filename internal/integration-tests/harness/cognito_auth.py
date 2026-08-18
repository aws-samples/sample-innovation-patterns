"""Mint a real Cognito identity token from the run's own user pool.

The **ID token** is returned, not the access token: only the ID token carries
``aud = client_id``, which makes it unambiguous under both auth layers — API
Gateway's JWT authorizer and ``app-lib``'s own middleware. Phase 1's preflight probe
already verified that this claim matches the deployed client id, so this module is
continuous with the probe rather than new.

**The password is the one secret this harness generates.** It is produced with
``secrets``, built by character class rather than by rejection sampling, and held in
memory only. Callers must register it with the transcript's redaction filter — see
``mint_token``'s return value.
"""

from __future__ import annotations

import base64
import json
import secrets
import string
from dataclasses import dataclass

from harness import aws


@dataclass(frozen=True)
class Identity:
    """A throwaway user and its identity token.

    ``password`` is returned so the caller can register it for redaction. It is not
    written to any file by this module.
    """

    username: str
    password: str
    id_token: str
    client_id: str


def generate_password(length: int = 20) -> str:
    """A password satisfying all four required character classes, by construction.

    ``cognito.yml``'s ``Policies.PasswordPolicy`` requires lowercase, uppercase,
    numbers and symbols — all four. Built by class rather than by rejection sampling,
    so it cannot fail intermittently against that policy.
    """
    symbols = "!@#$%^&*()-_=+"
    pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits, symbols]
    chars = [secrets.choice(p) for p in pools]
    alphabet = "".join(pools)
    chars += [secrets.choice(alphabet) for _ in range(length - len(pools))]
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def decode_payload(token: str) -> dict:
    """Decode a JWT payload WITHOUT verifying its signature.

    Narrowly deliberate: the token was minted seconds earlier by this module against
    the pool it names, and the only claim read is compared to a value from that same
    deployment. Never a pattern for anything that trusts an inbound token.
    """
    segment = token.split(".")[1]
    segment += "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment))


def mint_token(
    user_pool_id: str,
    client_id: str,
    region: str = aws.REGION,
) -> Identity:
    """Create a throwaway confirmed user and authenticate it.

    **This is the only write the live assertions make.** The user lives inside the
    run's own user pool, so the pool's own deletion removes it with no separate
    cleanup obligation.
    """
    idp = aws.session(region).client("cognito-idp")

    username = f"ipa-it-{secrets.token_hex(4)}@example.invalid"
    password = generate_password()

    idp.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        # No mail to a non-existent address.
        MessageAction="SUPPRESS",
        UserAttributes=[
            {"Name": "email", "Value": username},
            {"Name": "email_verified", "Value": "true"},
        ],
    )
    # Permanent=True clears FORCE_CHANGE_PASSWORD, which would otherwise answer
    # InitiateAuth with a NEW_PASSWORD_REQUIRED challenge rather than tokens.
    idp.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=username,
        Password=password,
        Permanent=True,
    )

    auth = idp.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
    )

    if "ChallengeName" in auth:
        raise AssertionError(
            f"adaptive authentication challenged InitiateAuth: "
            f"ChallengeName={auth['ChallengeName']!r} "
            f"ChallengeParameters={auth.get('ChallengeParameters')!r}. "
            "There is no fallback: ALLOW_ADMIN_USER_PASSWORD_AUTH is absent from the "
            "pool client's ExplicitAuthFlows."
        )

    id_token = auth.get("AuthenticationResult", {}).get("IdToken")
    if not id_token:
        raise AssertionError(
            f"no IdToken in AuthenticationResult: "
            f"{list(auth.get('AuthenticationResult', {}))}"
        )

    aud = decode_payload(id_token).get("aud")
    if aud != client_id:
        raise AssertionError(
            f"IdToken aud={aud!r} != UserPoolClientId={client_id!r}; the API "
            "Gateway authorizer will reject it"
        )

    return Identity(
        username=username, password=password, id_token=id_token, client_id=client_id
    )
