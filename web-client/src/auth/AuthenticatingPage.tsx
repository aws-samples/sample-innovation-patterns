// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { Spinner } from '@/components/ui/spinner'

export function AuthenticatingPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4 text-center">
        <Spinner className="size-8" />
        <div className="grid gap-1">
          <h2 className="text-lg font-semibold">Signing you in</h2>
          <p className="text-muted-foreground text-sm">
            Please wait while we authenticate your session.
          </p>
        </div>
      </div>
    </div>
  )
}
