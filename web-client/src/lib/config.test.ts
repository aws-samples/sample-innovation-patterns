// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { config } from './config'

describe('config', () => {
  it('reads from window.__CONFIG__', () => {
    // setup.ts sets window.__CONFIG__ with test defaults
    expect(config.LOG_LEVEL).toBe('silent')
    expect(config.OIDC_AUTHORITY).toBe('')
    expect(config.OIDC_CLIENT_ID).toBe('')
  })

  it('has features object with expected keys', () => {
    expect(config.features).toBeDefined()
    expect(config.features.jobs).toBe(true)
    expect(config.features.chat).toBe(false)
    expect(config.features.playground).toBe(true)
  })

  it('has API_BASE_URL', () => {
    expect(config).toHaveProperty('API_BASE_URL')
    expect(typeof config.API_BASE_URL).toBe('string')
  })

  it('has OIDC configuration fields', () => {
    expect(config).toHaveProperty('OIDC_AUTHORITY')
    expect(config).toHaveProperty('OIDC_CLIENT_ID')
    expect(config).toHaveProperty('OIDC_REDIRECT_URI')
    expect(config).toHaveProperty('OIDC_SCOPE')
    expect(config).toHaveProperty('OIDC_END_SESSION_ENDPOINT')
  })
})
