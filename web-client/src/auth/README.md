# OIDC Authentication

Frontend authentication using `@axa-fr/react-oidc` with Cognito.

## Configuration

Runtime config is read from `window.__CONFIG__` (set by `public/config.js`):

| Variable | Description |
|----------|-------------|
| `OIDC_AUTHORITY` | Cognito issuer URL (`https://cognito-idp.{region}.amazonaws.com/{poolId}`) |
| `OIDC_CLIENT_ID` | Cognito app client ID |
| `OIDC_REDIRECT_URI` | Callback URL after login |
| `OIDC_END_SESSION_ENDPOINT` | Cognito logout URL |

## Files

| File | Purpose |
|------|---------|
| `oidcConfig.ts` | OIDC configuration with Cognito workarounds |
| `AuthProvider.tsx` | React OIDC provider wrapper |
| `useAppAuth.ts` | Hook for login/logout/user state |
| `useAppUser.ts` | Hook for user claims |
| `RequireAuth.tsx` | Route guard component |
| `AuthenticatingPage.tsx` | Loading state during auth |

## Cognito Workarounds

Cognito's OIDC implementation has quirks:

1. **Missing `end_session_endpoint`** — Cognito's discovery document omits this. We provide `authority_configuration` manually in `oidcConfig.ts`.

2. **Logout requires extra params** — Cognito's `/logout` endpoint requires `client_id` and `logout_uri` query params. Handled in `useAppAuth.ts`:

```typescript
logout(undefined, {
  client_id: config.OIDC_CLIENT_ID,
  logout_uri: window.location.origin,
})
```

3. **OAuth endpoints on different domain** — The issuer URL (`cognito-idp.{region}.amazonaws.com`) differs from OAuth endpoints (`{prefix}.auth.{region}.amazoncognito.com`). We derive the OAuth domain from `OIDC_END_SESSION_ENDPOINT`.

## Usage

```typescript
import { useAppAuth } from '@/auth/useAppAuth'

function MyComponent() {
  const { isAuthenticated, login, logout, user } = useAppAuth()
  
  if (!isAuthenticated) {
    return <button onClick={login}>Login</button>
  }
  
  return (
    <div>
      <span>Welcome, {user?.name}</span>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

## Local Development

For local auth testing, create `public/config.local.js` with OIDC values. The Cognito stack must include `http://localhost:8080/authentication/callback` in its allowed callback URLs.

Use `configure-web-client-local` MCP tool to generate the config from a deployed Cognito stack.
