// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useOidc } from '@axa-fr/react-oidc'
import { useNavigate } from 'react-router'
import { config } from '@/lib/config'
import { isAuthEnabled } from './oidcConfig'

function useOidcAuth() {
  const oidc = useOidc()
  const cognitoLogout = () => {
    const extras: Record<string, string> = {}
    if (config.OIDC_END_SESSION_ENDPOINT) {
      extras['client_id'] = config.OIDC_CLIENT_ID
      extras['logout_uri'] = window.location.origin
    }
    return oidc.logout('/', extras)
  }
  return { logout: cognitoLogout, isAuthenticated: oidc.isAuthenticated }
}

function useNoAuth() {
  const navigate = useNavigate()
  return {
    logout: () => navigate('/login'),
    isAuthenticated: false,
  }
}

/** Use useOidcAuth when OIDC is configured, otherwise fall back to no-auth. */
export const useAppAuth = isAuthEnabled ? useOidcAuth : useNoAuth
