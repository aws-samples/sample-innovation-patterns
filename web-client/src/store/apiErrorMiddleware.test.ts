// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { vi } from 'vitest'

vi.mock('@axa-fr/oidc-client', () => ({
  OidcClient: { get: vi.fn() },
}))

import { OidcClient } from '@axa-fr/oidc-client'
import { apiErrorMiddleware } from './apiErrorMiddleware'

// Test the middleware function directly to avoid RTK Query reducer conflicts
function setupMiddleware() {
  const next = vi.fn((action: unknown) => action)
  const store = { dispatch: vi.fn(), getState: vi.fn() }
  const invoke = (apiErrorMiddleware as Function)(store)(next)
  return { invoke, next }
}

// Helper to create an action that isRejectedWithValue recognizes
function rejectedAction(status: number, message?: string) {
  return {
    type: 'api/executeQuery/rejected',
    payload: { status, data: { message } },
    meta: {
      rejectedWithValue: true,
      arg: {},
      requestId: 'test',
      requestStatus: 'rejected' as const,
    },
  }
}

describe('apiErrorMiddleware', () => {
  afterEach(() => {
    vi.mocked(OidcClient.get).mockReset()
  })

  it('triggers re-auth on 401 rejection', () => {
    const mockLoginAsync = vi.fn().mockResolvedValue(undefined)
    vi.mocked(OidcClient.get).mockReturnValue({
      loginAsync: mockLoginAsync,
    } as unknown as ReturnType<typeof OidcClient.get>)

    const { invoke, next } = setupMiddleware()
    invoke(rejectedAction(401, 'Unauthorized'))

    expect(mockLoginAsync).toHaveBeenCalled()
    expect(next).toHaveBeenCalled()
  })

  it('logs server error on 500', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const { invoke } = setupMiddleware()
    invoke(rejectedAction(500, 'Internal Server Error'))

    expect(consoleSpy).toHaveBeenCalledWith('Server error:', 'Internal Server Error')
    consoleSpy.mockRestore()
  })

  it('passes through non-rejected actions', () => {
    const { invoke, next } = setupMiddleware()
    const action = { type: 'some/action' }
    invoke(action)

    expect(next).toHaveBeenCalledWith(action)
  })

  it('does not trigger re-auth for non-401 errors', () => {
    const mockLoginAsync = vi.fn()
    vi.mocked(OidcClient.get).mockReturnValue({
      loginAsync: mockLoginAsync,
    } as unknown as ReturnType<typeof OidcClient.get>)

    const { invoke } = setupMiddleware()
    invoke(rejectedAction(403, 'Forbidden'))

    expect(mockLoginAsync).not.toHaveBeenCalled()
  })
})
