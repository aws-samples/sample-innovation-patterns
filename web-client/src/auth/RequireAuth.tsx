// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { OidcSecure } from '@axa-fr/react-oidc'
import { isAuthEnabled } from './oidcConfig'

export function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!isAuthEnabled) return <>{children}</>
  return <OidcSecure>{children}</OidcSecure>
}
