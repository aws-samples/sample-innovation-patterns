// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { isAuthEnabled, oidcConfiguration } from './oidcConfig'

describe('oidcConfig', () => {
  it('isAuthEnabled is false when no OIDC config', () => {
    // setup.ts sets empty OIDC_AUTHORITY and OIDC_CLIENT_ID
    expect(isAuthEnabled).toBe(false)
  })

  it('oidcConfiguration reads client_id from config', () => {
    expect(oidcConfiguration.client_id).toBe('')
  })

  it('oidcConfiguration sets redirect_uri from window.location', () => {
    expect(oidcConfiguration.redirect_uri).toContain('/authentication/callback')
  })

  it('oidcConfiguration sets scope', () => {
    expect(oidcConfiguration.scope).toBe('openid profile email')
  })

  it('does not include authority_configuration when no end_session_endpoint', () => {
    // With empty OIDC_END_SESSION_ENDPOINT, authority_configuration should not be set
    expect(oidcConfiguration).not.toHaveProperty('authority_configuration')
  })
})
