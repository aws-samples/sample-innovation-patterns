// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import type { ReactElement, ReactNode } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router'
import { FlagsProvider } from 'react-feature-flags'
import { baseApi } from '@/services/api/baseApi'
import { apiErrorMiddleware } from '@/store/apiErrorMiddleware'
import { getFlags } from '@/lib/featureFlags'

export function createTestStore() {
  return configureStore({
    reducer: { [baseApi.reducerPath]: baseApi.reducer },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware).concat(apiErrorMiddleware),
  })
}

interface WrapperOptions {
  store?: ReturnType<typeof createTestStore>
  route?: string
  flags?: Array<{ name: string; isActive: boolean }>
}

export function createWrapper({ store, route = '/', flags }: WrapperOptions = {}) {
  const testStore = store ?? createTestStore()
  const testFlags = flags ?? getFlags()

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <Provider store={testStore}>
        <FlagsProvider value={testFlags}>
          <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
        </FlagsProvider>
      </Provider>
    )
  }
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'>, WrapperOptions {}

export function renderWithProviders(ui: ReactElement, options: CustomRenderOptions = {}) {
  const { store, route, flags, ...renderOptions } = options
  const testStore = store ?? createTestStore()
  const wrapper = createWrapper({ store: testStore, route, flags })
  return {
    ...render(ui, { wrapper, ...renderOptions }),
    store: testStore,
    user: userEvent.setup(),
  }
}

// Re-export everything from testing-library for convenience
export { render, screen, waitFor, within, act } from '@testing-library/react'
export { renderHook } from '@testing-library/react'
export { userEvent }
