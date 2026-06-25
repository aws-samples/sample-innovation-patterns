// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      // Pin jsdom's origin to http://localhost (default is http://localhost:3000).
      // The shared MSW handlers (src/mocks/handlers.ts) use relative /api/v1/... paths,
      // which resolve against this origin. API_BASE_URL is 'http://localhost' in tests
      // (src/test/setup.ts), so RTK Query issues http://localhost/api/v1/... requests —
      // matching both the relative handlers and the absolute-URL server.use() overrides
      // in the page tests. Without this pin, the origin port mismatches (80 vs 3000).
      environmentOptions: {
        jsdom: {
          url: 'http://localhost',
        },
      },
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov'],
        include: ['src/**/*.{ts,tsx}'],
        exclude: [
          'src/test/**',
          'src/services/api/generated.ts',
          'src/components/ui/**',
          'src/vite-env.d.ts',
        ],
      },
    },
  }),
)
