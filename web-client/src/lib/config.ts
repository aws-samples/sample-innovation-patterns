/**
 * Runtime configuration accessor.
 *
 * Reads environment-specific config from window.__CONFIG__, which is set by
 * public/config.js (loaded via <script> tag in index.html before the app bundle).
 *
 * In local dev, copy config.template.js to config.js. Values are empty/default —
 * the Vite proxy handles API routing. For local auth testing, create config.local.js
 * with OIDC_AUTHORITY and OIDC_CLIENT_ID (see docs/docs/solution/web-client/LOCAL_AUTH.md).
 *
 * In production, config_helper.py or the configure-web-client MCP tool writes
 * the real values into dist/config.js at deploy time.
 *
 * To add a new config value:
 *   1. Add the key to public/config.template.js with a default
 *   2. Add the key to the AppConfig interface below
 *   3. Add the key to the fallback object below
 *   4. Import { config } from '@/lib/config' and use config.YOUR_KEY
 *
 * See: docs/docs/solution/web-client/CONFIG.md
 */

interface FeatureFlags {
  chat: boolean
  jobs: boolean
  playground: boolean
  kb_playground: boolean
  kitchen_sink: boolean
}

interface AppConfig {
  API_BASE_URL: string
  OIDC_AUTHORITY: string
  OIDC_CLIENT_ID: string
  OIDC_REDIRECT_URI: string
  OIDC_SCOPE: string
  OIDC_END_SESSION_ENDPOINT: string
  LOG_LEVEL: string
  features: FeatureFlags
}

declare global {
  interface Window {
    __CONFIG__?: AppConfig
  }
}

export const config: AppConfig = window.__CONFIG__ ?? {
  API_BASE_URL: '',
  OIDC_AUTHORITY: '',
  OIDC_CLIENT_ID: '',
  OIDC_REDIRECT_URI: '',
  OIDC_SCOPE: 'openid profile email',
  OIDC_END_SESSION_ENDPOINT: '',
  LOG_LEVEL: 'debug',
  features: {
    chat: false,
    jobs: false,
    playground: true,
    kb_playground: false,
    kitchen_sink: true,
  },
}

console.log('[config]', config)
