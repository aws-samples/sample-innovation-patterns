// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// Runtime configuration — local development defaults.
//
// This file is committed to the repo with sensible defaults for local dev:
//   - API_BASE_URL is empty — the Vite proxy forwards /api to localhost:8000
//   - OIDC fields are empty — auth is disabled
//   - Feature flags enable playground and kitchen_sink
//
// For local auth testing, create public/config.local.js with your Cognito
// values (loaded only on localhost, gitignored).
//
// In production, dist/config.js is overwritten at deploy time by
// config_helper.py or the configure-web-client MCP tool.
// See config.production-example.js for the full list of configurable values.
window.__CONFIG__ = {
  API_BASE_URL: "",
  OIDC_AUTHORITY: "",
  OIDC_CLIENT_ID: "",
  OIDC_REDIRECT_URI: "",
  OIDC_SCOPE: "openid profile email",
  LOG_LEVEL: "debug",
  // Feature flags: toggle UI features on/off. Set to true to show, false to hide.
  // These control sidebar navigation visibility only — routes remain accessible via URL.
  features: {
    chat: false,
    jobs: false,
    playground: true,
    kb_playground: false,
    kitchen_sink: true,
  },
};
