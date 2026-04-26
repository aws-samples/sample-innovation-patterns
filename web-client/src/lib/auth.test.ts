// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { vi } from 'vitest'

vi.mock('@axa-fr/oidc-client', () => ({
  OidcClient: {
    get: vi.fn(),
  },
}))

import { OidcClient } from '@axa-fr/oidc-client'
import { getIdToken } from './auth'

describe('getIdToken', () => {
  afterEach(() => {
    vi.mocked(OidcClient.get).mockReset()
  })

  it('returns token when available', () => {
    vi.mocked(OidcClient.get).mockReturnValue({
      tokens: { idToken: 'test-token-123' },
    } as unknown as ReturnType<typeof OidcClient.get>)

    expect(getIdToken()).toBe('test-token-123')
  })

  it('returns undefined when OidcClient returns null', () => {
    vi.mocked(OidcClient.get).mockReturnValue(null as unknown as ReturnType<typeof OidcClient.get>)

    expect(getIdToken()).toBeUndefined()
  })

  it('returns undefined when tokens is undefined', () => {
    vi.mocked(OidcClient.get).mockReturnValue({
      tokens: undefined,
    } as unknown as ReturnType<typeof OidcClient.get>)

    expect(getIdToken()).toBeUndefined()
  })

  it('returns undefined when OidcClient.get throws', () => {
    vi.mocked(OidcClient.get).mockImplementation(() => {
      throw new Error('not initialized')
    })

    expect(getIdToken()).toBeUndefined()
  })
})
