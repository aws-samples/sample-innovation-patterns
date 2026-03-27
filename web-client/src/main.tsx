import { setupLogging } from '@/lib/setupLogging'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
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
        <AuthProvider>
          <ApiProvider>
            <RouterProvider router={router} />
            <Toaster />
          </ApiProvider>
        </AuthProvider>
      </ActiveThemeProvider>
    </ThemeProvider>
  </StrictMode>,
)
