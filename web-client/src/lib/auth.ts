// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { OidcClient } from '@axa-fr/oidc-client'

/** Get the current Cognito ID token for API authorization, or undefined if auth is disabled. */
export function getIdToken(): string | undefined {
  try {
    return OidcClient.get()?.tokens?.idToken ?? undefined
  } catch {
    return undefined
  }
}
