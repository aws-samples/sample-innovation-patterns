// Runtime configuration template for the web-client.
//
// SETUP:
//   cp public/config.template.js public/config.js
//
// Or use the MCP tool:
//   configure-web-client-local (reads from your deployed Cognito stack)
//
// LOCAL DEV (no auth): Use as-is. API_BASE_URL is empty — the Vite proxy
// forwards /api requests to localhost:8000.
//
// LOCAL DEV (with auth): Also create public/config.local.js with your
// Cognito values. See docs/docs/solution/web-client/LOCAL_AUTH.md.
//
// PRODUCTION: The configure-web-client MCP tool overwrites dist/config.js
// at deploy time. This file is never deployed.
window.__CONFIG__ = {
  API_BASE_URL: "",
  OIDC_AUTHORITY: "",
  OIDC_CLIENT_ID: "",
  OIDC_REDIRECT_URI: "",
  OIDC_SCOPE: "openid profile email",
  LOG_LEVEL: "debug",
};
