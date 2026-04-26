// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
/**
 * Console log-level gating based on runtime configuration.
 *
 * Overrides `console.debug`, `console.log`, `console.info`, `console.warn`,
 * and `console.error` so that calls below the configured threshold become
 * silent no-ops. This lets production builds suppress verbose output without
 * changing application code.
 *
 * ## How it works
 *
 * 1. Reads `LOG_LEVEL` from `window.__CONFIG__` (set by `public/config.js`
 *    before the app bundle loads).
 * 2. Captures references to the **original** console methods.
 * 3. Replaces each method with either the original (bound) or a no-op,
 *    depending on whether its severity meets the threshold.
 *
 * Because the originals are captured first, the replacement methods never
 * call back into the overridden versions — no circular recursion.
 *
 * ## Levels (ascending severity)
 *
 * | Value       | Numeric | Visible methods                        |
 * |-------------|---------|----------------------------------------|
 * | `"debug"`   | 0       | debug, log, info, warn, error          |
 * | `"info"`    | 1       | log, info, warn, error                 |
 * | `"warning"` | 2       | warn, error                            |
 * | `"error"`   | 3       | error                                  |
 * | `"silent"`  | 4       | none                                   |
 *
 * ## Configuration
 *
 * Set `LOG_LEVEL` in `public/config.js` (local dev) or in the deployed
 * `dist/config.js` (production). The default fallback is `"debug"`.
 *
 * ```js
 * // public/config.js
 * window.__CONFIG__ = {
 *   API_BASE_URL: "",
 *   LOG_LEVEL: "warning",  // production: only warn + error
 * };
 * ```
 *
 * ## Usage
 *
 * Call once at the top of `main.tsx`, before `createRoot()`:
 *
 * ```ts
 * import { setupLogging } from "@/lib/setupLogging";
 * setupLogging();
 * ```
 *
 * After this call, all `console.*` usage throughout the app — including
 * third-party libraries — is subject to the configured threshold.
 */
import { config } from '@/lib/config'

const LEVELS: Record<string, number> = {
  debug: 0,
  info: 1,
  warning: 2,
  warn: 2,
  error: 3,
  silent: 4,
}

const noop = () => {}

export function setupLogging() {
  const threshold = LEVELS[config.LOG_LEVEL] ?? LEVELS.info
  const _console = {
    log: console.log,
    debug: console.debug,
    info: console.info,
    warn: console.warn,
    error: console.error,
  }

  console.debug = threshold <= LEVELS.debug ? _console.debug.bind(console) : noop
  console.log = threshold <= LEVELS.info ? _console.log.bind(console) : noop
  console.info = threshold <= LEVELS.info ? _console.info.bind(console) : noop
  console.warn = threshold <= LEVELS.warning ? _console.warn.bind(console) : noop
  console.error = threshold <= LEVELS.error ? _console.error.bind(console) : noop

  _console.info(`[logging] level=${config.LOG_LEVEL}, threshold=${threshold}`)
}
