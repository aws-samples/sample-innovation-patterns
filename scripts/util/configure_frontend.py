#!/usr/bin/env python3
"""Generate web-client/dist/config.js with runtime configuration.

Writes the window.__CONFIG__ object consumed by the React frontend.
Called from scripts/post-deploy.mk after all stacks are deployed.

Usage:
    python3 scripts/util/configure_frontend.py \
        --api-base-url "https://xxx.execute-api..." \
        --oidc-authority "https://cognito-idp..." \
        --oidc-client-id "abc123" \
        --oidc-redirect-uri "https://dxxx.cloudfront.net/authentication/callback" \
        --oidc-end-session-endpoint "https://xxx.auth.us-east-1.amazoncognito.com/logout" \
        --output web-client/dist/config.js
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate config.js for web-client")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--oidc-authority", required=True)
    parser.add_argument("--oidc-client-id", required=True)
    parser.add_argument("--oidc-redirect-uri", required=True)
    parser.add_argument("--oidc-end-session-endpoint", required=True)
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--enable-feature",
        action="append",
        default=[],
        help="Enable a feature flag (repeatable, e.g. --enable-feature jobs)",
    )
    args = parser.parse_args()

    # Fail early if dist/ doesn't contain a built frontend (Q2:A)
    output = Path(args.output)
    index_html = output.parent / "index.html"
    if not index_html.exists():
        print(
            f"[configure_frontend] ERROR: {index_html} not found. "
            "Run 'make -f scripts/build.mk build-frontend' first.",
            file=__import__("sys").stderr,
        )
        raise SystemExit(1)

    config = {
        "API_BASE_URL": args.api_base_url,
        "OIDC_AUTHORITY": args.oidc_authority,
        "OIDC_CLIENT_ID": args.oidc_client_id,
        "OIDC_REDIRECT_URI": args.oidc_redirect_uri,
        "OIDC_SCOPE": "openid profile email",
        "OIDC_END_SESSION_ENDPOINT": args.oidc_end_session_endpoint,
        "LOG_LEVEL": "debug",
        "features": {
            "chat": False,
            "jobs": False,
            "playground": True,
            "kb_playground": False,
            "kitchen_sink": True,
        },
    }
    for feat in args.enable_feature:
        config["features"][feat] = True
    output.write_text(
        f"window.__CONFIG__ = {json.dumps(config, indent=2)};\n"
    )
    print(f"[configure_frontend] Wrote {output}")


if __name__ == "__main__":
    main()
