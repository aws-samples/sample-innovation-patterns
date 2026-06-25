// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
// Node (Vitest) MSW server. Reuses the shared handler set from src/mocks/handlers.ts
// — the same handlers the browser worker (src/mocks/browser.ts) registers in dev.
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'

export const server = setupServer(...handlers)
