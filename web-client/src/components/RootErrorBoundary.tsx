// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useRouteError, isRouteErrorResponse, Link } from 'react-router'
import { IconAlertTriangle, IconArrowLeft, IconRefresh, IconCopy } from '@tabler/icons-react'
import { Button } from '@/components/ui/button'

export function RootErrorBoundary() {
  const error = useRouteError()
  const showDetails = import.meta.env.DEV

  let title = 'Something broke'
  let message = 'We hit an unexpected error on this page.'
  let status: number | undefined
  let details: string | undefined
  let stack: string | undefined

  if (isRouteErrorResponse(error)) {
    status = error.status
    title = error.status === 404 ? 'Page not found' : `Error ${error.status}`
    message =
      error.status === 404
        ? 'The page you\u2019re looking for doesn\u2019t exist or has been moved.'
        : error.statusText || message
    details = typeof error.data === 'string' ? error.data : JSON.stringify(error.data)
  } else if (error instanceof Error) {
    details = error.message
    stack = error.stack
  }

  const diagnosticText = [
    details && `Error: ${details}`,
    `Route: ${window.location.pathname}`,
    stack && `\n${stack}`,
  ]
    .filter(Boolean)
    .join('\n')

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-md space-y-8 text-center">
        <div className="flex justify-center">
          <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-4 dark:bg-destructive/10">
            <IconAlertTriangle className="size-8 animate-pulse text-destructive" stroke={1.5} />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="text-muted-foreground text-sm leading-relaxed">
            {message}
            <br />
            This has been noted — try one of these:
          </p>
        </div>

        <div className="flex justify-center gap-3">
          <Button variant="default" asChild>
            <Link to="/">
              <IconArrowLeft className="size-4" />
              Back to Dashboard
            </Link>
          </Button>
          <Button variant="outline" onClick={() => window.location.reload()}>
            <IconRefresh className="size-4" />
            Reload
          </Button>
        </div>

        {showDetails && details && (
          <>
            <div className="border-t border-dashed" />
            <details className="group text-left">
              <summary className="text-muted-foreground hover:text-foreground cursor-pointer select-none text-xs transition-colors">
                Diagnostic details
              </summary>
              <div className="relative mt-3 rounded-lg border bg-card p-4">
                <pre className="text-muted-foreground max-h-64 overflow-auto break-all font-mono text-xs whitespace-pre-wrap">
                  {diagnosticText}
                </pre>
                <Button
                  variant="ghost"
                  size="xs"
                  className="text-muted-foreground absolute top-2 right-2"
                  onClick={() => void navigator.clipboard.writeText(diagnosticText)}
                >
                  <IconCopy className="size-3" />
                  Copy
                </Button>
              </div>
            </details>
          </>
        )}

        <p className="text-muted-foreground/40 font-mono text-[10px]">
          {status && <span className="mr-2">HTTP {status}</span>}
          app v{__APP_VERSION__} · {__BUILD_VERSION__}
        </p>
      </div>
    </div>
  )
}
