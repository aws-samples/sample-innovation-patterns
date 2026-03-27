import { config } from '@/lib/config'

// Derive the Cognito Hosted UI base URL from the end_session_endpoint.
// Cognito OAuth endpoints (authorize, token, etc.) live on the Hosted UI domain,
// NOT on the issuer URL. The issuer is cognito-idp.{region}.amazonaws.com/{poolId}
// but OAuth endpoints are {prefix}.auth.{region}.amazoncognito.com/oauth2/*.
const cognitoDomainBase = config.OIDC_END_SESSION_ENDPOINT
  ? config.OIDC_END_SESSION_ENDPOINT.replace(/\/logout$/, '')
  : ''

export const oidcConfiguration = {
  client_id: config.OIDC_CLIENT_ID,
  redirect_uri: config.OIDC_REDIRECT_URI || window.location.origin + '/authentication/callback',
  silent_redirect_uri: window.location.origin + '/authentication/silent-callback',
  scope: config.OIDC_SCOPE || 'openid profile email',
  authority: config.OIDC_AUTHORITY,
  service_worker_only: false,
  // Cognito's OIDC discovery doc omits end_session_endpoint, and its /logout
  // endpoint requires client_id + logout_uri which the OIDC spec doesn't include.
  // We provide the full authority_configuration so the library knows where to
  // redirect on logout. The extra Cognito params (client_id, logout_uri) are
  // passed via logout() extras in useAppAuth.ts.
  ...(cognitoDomainBase && {
    authority_configuration: {
      authorization_endpoint: `${cognitoDomainBase}/oauth2/authorize`,
      token_endpoint: `${cognitoDomainBase}/oauth2/token`,
      revocation_endpoint: `${cognitoDomainBase}/oauth2/revoke`,
      userinfo_endpoint: `${cognitoDomainBase}/oauth2/userInfo`,
      end_session_endpoint: config.OIDC_END_SESSION_ENDPOINT,
      issuer: config.OIDC_AUTHORITY,
    },
  }),
}

/** True when OIDC config is provided (production). False in local dev. */
export const isAuthEnabled = Boolean(config.OIDC_AUTHORITY && config.OIDC_CLIENT_ID)
