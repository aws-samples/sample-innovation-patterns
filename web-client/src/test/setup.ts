// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll } from 'vitest'
import { server } from './msw/server'

// Default window.__CONFIG__ for all tests — auth disabled, silent logging
window.__CONFIG__ = {
  API_BASE_URL: 'http://localhost',
  OIDC_AUTHORITY: '',
  OIDC_CLIENT_ID: '',
  OIDC_REDIRECT_URI: '',
  OIDC_SCOPE: 'openid profile email',
  OIDC_END_SESSION_ENDPOINT: '',
  LOG_LEVEL: 'silent',
  features: {
    chat: false,
    jobs: true,
    playground: true,
    kb_playground: false,
    kitchen_sink: false,
  },
}

// Mock matchMedia for hooks that use it (use-mobile.ts)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// MSW server lifecycle
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
})
afterAll(() => server.close())
