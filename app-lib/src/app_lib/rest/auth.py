"""JWT authentication middleware for the REST API.

Validates Bearer tokens against any OIDC-compliant identity provider.
Enable by setting AUTH_ENABLED=true and providing AUTH_ISSUER + AUTH_AUDIENCE.
"""

import json
import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() == "true"
AUTH_ISSUER = os.environ.get("AUTH_ISSUER", "")
AUTH_AUDIENCE = os.environ.get("AUTH_AUDIENCE", "")
AUTH_ALGORITHMS = os.environ.get("AUTH_ALGORITHMS", "RS256").split(",")

PUBLIC_PATHS = {"/health", "/version", "/docs", "/openapi.json"}


@lru_cache
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(f"{AUTH_ISSUER}/.well-known/jwks.json")


def _check_audience(claims: dict) -> bool:
    """Validate audience. Handles Cognito (client_id) and standard OIDC (aud as str or list)."""
    aud = claims.get("aud")
    if aud is not None:
        if isinstance(aud, list):
            return AUTH_AUDIENCE in aud
        return aud == AUTH_AUDIENCE
    return claims.get("client_id") == AUTH_AUDIENCE


def _json_401(detail: str) -> Response:
    return Response(
        content=json.dumps({"detail": detail}),
        status_code=401,
        media_type="application/json",
    )


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Bearer tokens on all routes except PUBLIC_PATHS."""

    async def dispatch(self, request: Request, call_next):
        """Validate JWT token and forward the request."""
        if (
            not AUTH_ENABLED
            or request.url.path in PUBLIC_PATHS
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return _json_401("Missing Bearer token")

        token = auth_header[7:]

        try:
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=AUTH_ALGORITHMS,
                issuer=AUTH_ISSUER,
                options={"verify_aud": False, "verify_exp": True, "verify_iss": True},
            )
        except jwt.ExpiredSignatureError:
            return _json_401("Token expired")
        except jwt.InvalidTokenError as e:
            return _json_401(f"Invalid token: {e}")

        if not _check_audience(claims):
            return _json_401("Invalid audience")

        request.state.user = claims
        return await call_next(request)
