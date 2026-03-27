import { useOidcUser } from '@axa-fr/react-oidc'
import { isAuthEnabled } from './oidcConfig'

const fallbackUser = { name: 'Developer', email: 'dev@localhost' }

function useOidcAppUser() {
  const { oidcUser } = useOidcUser()
  return {
    name: oidcUser?.name ?? oidcUser?.preferred_username ?? 'User',
    email: oidcUser?.email ?? '',
  }
}

function useNoAuthUser() {
  return fallbackUser
}

/** Use OIDC user info when configured, otherwise return fallback dev user. */
export const useAppUser = isAuthEnabled ? useOidcAppUser : useNoAuthUser
