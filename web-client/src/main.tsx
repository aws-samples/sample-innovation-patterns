// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { setupLogging } from '@/lib/setupLogging'
import { config } from '@/lib/config'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { FlagsProvider } from 'flagged'
import { ActiveThemeProvider } from '@/components/active-theme'
import { AuthProvider } from '@/auth/AuthProvider'
import { ApiProvider } from '@/providers/ApiProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { Toaster } from '@/components/ui/sonner'
import { routes } from '@/routes'
import './index.css'

setupLogging()

// Mock-UX mode: when MOCK_API is true (non-production only), start the MSW browser
// worker so /api/v1/* is served from src/mocks/handlers.ts with no backend running.
// The worker is lazy-imported so MSW is code-split out of the production bundle, and
// the import.meta.env.PROD guard ensures mocking can never start in a prod build even
// if MOCK_API were somehow true. See src/mocks/AGENTS.md and web-client/CLAUDE.md.
async function enableMocking() {
  if (import.meta.env.PROD || !config.MOCK_API) return
  const { worker } = await import('@/mocks/browser')
  await worker.start({ onUnhandledRequest: 'warn' })
}

const router = createBrowserRouter(routes)

void enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ThemeProvider>
        <ActiveThemeProvider>
          <FlagsProvider features={config.features}>
            <AuthProvider>
              <ApiProvider>
                <RouterProvider router={router} />
                <Toaster />
              </ApiProvider>
            </AuthProvider>
          </FlagsProvider>
        </ActiveThemeProvider>
      </ThemeProvider>
    </StrictMode>,
  )
})
