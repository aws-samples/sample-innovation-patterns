# mocks/

MSW (Mock Service Worker) collateral shared between the browser dev worker and the
Node test server. This directory is the mechanism behind **mock-UX mode** — the
ability to build and iterate on the web-client's UX against mocked API responses
before any backend exists.

## Files

| File | Role |
|---|---|
| `handlers.ts` | The shared request handlers. One flat array, **relative** `/api/v1/...` URLs. The single source of truth for both dev and tests. |
| `browser.ts` | `setupWorker(...handlers)` — the browser worker, started conditionally from `src/main.tsx`. |
| `../test/msw/server.ts` | `setupServer(...handlers)` — the Node worker for Vitest. Imports the same `handlers`. |
| `../../public/mockServiceWorker.js` | Generated worker script (via `npx msw init public/` in `postinstall`). Gitignored. Do not edit. |

## Mode detection

The canonical signal is **`config.MOCK_API === true`** (`window.__CONFIG__.MOCK_API`,
read through `@/lib/config`). When true and the build is non-production, `main.tsx`
lazy-imports `browser.ts` and starts the worker before rendering. A build-time
`import.meta.env.PROD` guard ensures the worker can never start in a production
build, and the deploy writer (`infra/scripts/configure_frontend.py`) always writes
`MOCK_API: false`. Mocking therefore cannot ship enabled.

`MOCK_API` is a top-level config key (a *data-source* switch), **not** a
`features.*` flag (those are product-visibility switches). The two are independent —
see `web-client/CLAUDE.md` § Mock-UX mode.

## The three-stage UX-first loop

1. **Enter mock-UX mode** — set `MOCK_API: true` in `public/config.js` (or
   `config.local.js`), run `npm run dev`. The worker intercepts `/api/v1/*`; no
   backend needed.
2. **Iterate on mock UX** — build a page, then author/maintain its handler here in
   the same change, returning realistic DTO-shaped JSON. Gate in-progress features
   behind a `features.*` flag so they can ship dark.
3. **Scaffold the real backend from this collateral** — turn a handler into an
   `app-lib` feature whose `routes/{name}_dto.py` Pydantic shape mirrors the handler
   JSON, run the backend, `npm run codegen` to re-type the RTK Query client, then
   flip `MOCK_API` off. The same screens now hit real services.

## Why relative URLs

A relative `/api/v1/...` path resolves against:

- `location.origin` in the browser (dev), and
- jsdom's origin `http://localhost` under Vitest (pinned in `vitest.config.ts`),
  where `API_BASE_URL` is `http://localhost` so RTK Query issues matching absolute
  requests MSW intercepts by path.

This is the one detail that lets a single handler set serve both environments. Absolute
URLs (`http://localhost/api/v1/...`) still work in `server.use()` overrides inside
individual test files because the test origin is pinned to the same host.

## The handler is the contract

For the mock→real loop to be lossless, a handler's response shape must match how the
corresponding `app-lib` feature serializes its DTO (`routes/{name}_dto.py`). Author
handlers as if a real Pydantic model produced them; then Stage 3 is a near-drop-in.
See `app-lib/src/app_lib/features/CLAUDE.md` for the reverse-path (feature-from-handler)
recipe, and `docs/.../developer-docs/web-client/ux-first-mocking.md` for the full guide.
