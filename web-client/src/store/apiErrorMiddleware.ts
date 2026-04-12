// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { isRejectedWithValue } from '@reduxjs/toolkit'
import type { Middleware } from '@reduxjs/toolkit'
import { OidcClient } from '@axa-fr/oidc-client'

interface ApiErrorPayload {
  status?: number
  data?: { message?: string }
}

export const apiErrorMiddleware: Middleware = () => (next) => (action) => {
  if (isRejectedWithValue(action)) {
    const payload = action.payload as ApiErrorPayload
    if (payload?.status === 401) {
      console.warn('Unauthorized — triggering re-authentication')
      try {
        void OidcClient.get()?.loginAsync(window.location.pathname)
      } catch {
        // Auth not enabled
      }
    }
    if (payload?.status === 500) {
      console.error('Server error:', payload?.data?.message)
    }
  }
  return next(action)
}
