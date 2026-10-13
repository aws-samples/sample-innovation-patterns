# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for JWTAuthMiddleware token validation."""

import time
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

ISSUER = "https://issuer.example.com"
AUDIENCE = "test-client-id"


@pytest.fixture(scope="module")
def private_key():
    """Generate an RSA key pair for signing test tokens."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def client(private_key, monkeypatch):
    """Create a test client whose JWKS lookup returns the test public key."""
    # auth reads AUTH_ENABLED once, at import. The route-test clients import the
    # app with it set to "false" and assume they are first, so import it the
    # same way here and enable auth only on the patched module attribute.
    monkeypatch.setenv("AUTH_ENABLED", "false")
    from app_lib.common import auth
    from app_lib.common.auth import JWTAuthMiddleware

    signing_key = MagicMock()
    signing_key.key = private_key.public_key()
    jwks_client = MagicMock()
    jwks_client.get_signing_key_from_jwt.return_value = signing_key

    monkeypatch.setattr(auth, "AUTH_ENABLED", True)
    monkeypatch.setattr(auth, "AUTH_ISSUER", ISSUER)
    monkeypatch.setattr(auth, "AUTH_AUDIENCE", AUDIENCE)
    monkeypatch.setattr(auth, "_jwks_client", lambda: jwks_client)

    app = FastAPI()
    app.add_middleware(JWTAuthMiddleware)

    @app.get("/protected")
    def protected(request: Request):
        return request.state.user

    return TestClient(app)


def _token(private_key, **overrides):
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "user-1",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


def _get(client, token):
    return client.get("/protected", headers={"Authorization": f"Bearer {token}"})


def test_valid_token_accepted(client, private_key):
    """Test a correctly signed, unexpired token from the issuer is accepted."""
    resp = _get(client, _token(private_key))
    assert resp.status_code == 200
    assert resp.json()["sub"] == "user-1"


def test_expired_token_rejected(client, private_key):
    """Test a token whose exp is in the past is rejected."""
    resp = _get(client, _token(private_key, exp=int(time.time()) - 60))
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expired"


def test_wrong_issuer_rejected(client, private_key):
    """Test a token from a different issuer is rejected."""
    resp = _get(client, _token(private_key, iss="https://other.example.com"))
    assert resp.status_code == 401
    assert resp.json()["detail"].startswith("Invalid token")
