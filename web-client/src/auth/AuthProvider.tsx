// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { OidcProvider } from '@axa-fr/react-oidc'
import type { ReactNode } from 'react'
import { oidcConfiguration, isAuthEnabled } from './oidcConfig'
import { AuthenticatingPage } from './AuthenticatingPage'

export function AuthProvider({ children }: { children: ReactNode }) {
  if (!isAuthEnabled) {
    return <>{children}</>
  }
  return (
    <OidcProvider
      configuration={oidcConfiguration}
      authenticatingComponent={AuthenticatingPage}
      callbackSuccessComponent={AuthenticatingPage}
      loadingComponent={AuthenticatingPage}
      sessionLostComponent={AuthenticatingPage}
    >
      {children}
    </OidcProvider>
  )
}
