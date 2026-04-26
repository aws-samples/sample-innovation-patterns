// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { setupLogging } from '@/lib/setupLogging'
import { getFlags } from '@/lib/featureFlags'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { FlagsProvider } from 'react-feature-flags'
import { ActiveThemeProvider } from '@/components/active-theme'
import { AuthProvider } from '@/auth/AuthProvider'
import { ApiProvider } from '@/providers/ApiProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { Toaster } from '@/components/ui/sonner'
import { routes } from '@/routes'
import './index.css'

setupLogging()

const router = createBrowserRouter(routes)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <ActiveThemeProvider>
        <FlagsProvider value={getFlags()}>
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
