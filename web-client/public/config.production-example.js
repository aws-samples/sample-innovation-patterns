// Production configuration example for the web-client.
//
// This file shows all configurable values and their expected format.
// At deploy time, config_helper.py or the configure-web-client MCP tool
// overwrites dist/config.js with real values (Cognito endpoints, API URL, etc.).
//
// For local development, public/config.js is committed with sensible defaults.
// You do NOT need to copy or modify this file for local dev.
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
