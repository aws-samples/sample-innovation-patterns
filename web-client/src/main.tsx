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

const router = createBrowserRouter(routes)

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
