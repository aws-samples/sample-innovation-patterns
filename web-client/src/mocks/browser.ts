// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
//
// Browser MSW worker. Reuses the same handler set as the Node test server
// (src/mocks/handlers.ts) so mock behavior is identical in dev and tests.
//
// Started conditionally from src/main.tsx — only when MOCK_API is true and the
// build is non-production. See main.tsx `enableMocking()` and src/mocks/AGENTS.md.
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export const worker = setupWorker(...handlers)
