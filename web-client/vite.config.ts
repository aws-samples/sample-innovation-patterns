// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { execSync } from 'child_process'
import { readFileSync } from 'node:fs'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Resolve the frontend version JS-natively (no python3 dependency at build time).
// `isBuild` is true only for `vite build` (npm run build); vitest and `vite` dev do
// not pass the `build` verb, so they fall back gracefully instead of throwing.
// NOTE: this config export MUST stay an object literal — vitest.config.ts does
// `mergeConfig(viteConfig, ...)`, which throws on a callback/function config.
const isBuild = process.argv.includes('build')

function failOrFallback(kind: 'version' | 'sha'): string {
  if (isBuild) throw new Error(`vite.config: failed to resolve ${kind}`)
  console.warn(`vite.config: ${kind} unresolved; using fallback`)
  return kind === 'sha' ? 'unknown' : '0.0.0'
}

// Version source of truth for the frontend artifact: web-client/package.json
// (kept equal to app-lib/pyproject.toml at release time; no auto-sync).
function getAppVersion(): string {
  try {
    const pkg = JSON.parse(readFileSync(path.resolve(__dirname, 'package.json'), 'utf-8')) as {
      version?: string
    }
    if (!pkg.version) return failOrFallback('version')
    return pkg.version
  } catch {
    return failOrFallback('version')
  }
}

// SHA from CodeBuild (CODEBUILD_RESOLVED_SOURCE_VERSION) when present, else local git.
function getSha(): string {
  const cb = process.env.CODEBUILD_RESOLVED_SOURCE_VERSION
  if (cb) return cb.slice(0, 7)
  try {
    return execSync('git rev-parse --short=7 HEAD').toString().trim()
  } catch {
    return failOrFallback('sha')
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(getAppVersion()),
    __BUILD_VERSION__: JSON.stringify(getSha()),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/version': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
