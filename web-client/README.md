# web-client

React 19 + TypeScript SPA with Vite, RTK Query, and OpenAPI codegen. Consumes the FastAPI backend (`app-lib/`) via REST and SSE.

## Prerequisites

- Node.js 22+
- For full-stack dev: backend running on port 8000 — see the [Quickstart](/getting-started/quickstart) or run `make dev-backend` from the project root

## Quick Start

```bash
npm install         # Install dependencies
npm run dev         # Vite dev server on :8080 (proxies /api → :8000)
```

Or from the project root: `make dev` starts both backend and frontend.

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 8080 (proxies `/api` → localhost:8000) |
| `npm run build` | Type-check + production build |
| `npm run codegen` | Fetch OpenAPI schema + generate typed API client |
| `npm run update:openapi` | Fetch OpenAPI schema only |
| `npm run generate:api` | Regenerate client from existing schema |
| `make lint` | Format + lint with auto-fix (local development) |
| `make lint-cicd` | Check format + lint without fixing (CI gate) |

## Runtime Config

`public/config.js` is committed with local-dev defaults — no setup needed. Auth is disabled and the Vite proxy handles API routing.

| File | Purpose | Tracked |
|------|---------|---------|
| `config.js` | Local-dev defaults (committed) | Yes |
| `config.local.js` | Optional OIDC overrides for localhost auth testing | No (gitignored) |
| `config.production-example.js` | Reference for production deploy-time values | Yes |

To test with Cognito auth locally, create `public/config.local.js`:

```javascript
window.__CONFIG__ = {
  ...window.__CONFIG__,
  OIDC_AUTHORITY: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXX",
  OIDC_CLIENT_ID: "your-client-id",
};
```

This file is loaded only when `location.hostname === 'localhost'` and is gitignored.

## Codegen Pipeline

Running `npm run codegen` performs two steps:

1. Downloads the OpenAPI spec from `http://localhost:8000/openapi.json` into `openapi-schema.json`
2. Runs `@rtk-query/codegen-openapi` using `openapi-config.cjs` to produce `src/services/api/generated.ts`

The generated file contains typed endpoints, React hooks, and TypeScript types for every route in the FastAPI app.

> [!CAUTION]
> Do not edit `generated.ts` manually. It is overwritten on every codegen run.

The backend **must be running** at localhost:8000 for `npm run codegen` to work. The `generated.ts` file is committed — codegen is only needed when backend routes change.

## Format & Lint

The project uses Prettier for formatting and ESLint with type-aware rules for linting.

- `make lint` — Run during development. Formats all files with Prettier, then runs ESLint with `--fix`.
- `make lint-cicd` — Run in CI. Checks formatting and lint without modifying files. Exits non-zero on violations.

VS Code users: install `dbaeumer.vscode-eslint` and `rvest.vs-code-prettier-eslint`, then copy `.vscode/settings.json.example` to `.vscode/settings.json` for format-on-save.

## Directory Layout

```
src/
├── main.tsx            # Entry point: setupLogging, createRoot, provider tree
├── routes.ts           # Route table (plain .ts, RouteObject[])
├── index.css           # Global styles
├── auth/               # OIDC auth module (config + provider)
├── components/         # Shared UI components
│   └── ui/             # shadcn/ui primitives (Button, Card, etc.)
├── hooks/              # Shared React hooks used by 2+ pages
├── layouts/            # Structural shells with <Outlet /> for react-router
├── lib/                # Framework-agnostic utilities (no React imports)
├── pages/              # Route-level page components (one per route)
├── providers/          # React context providers (Redux, future auth)
├── services/api/       # RTK Query API layer (see services/api/README.md)
└── store/              # Redux store, typed hooks, error middleware
```

## Extending

### When the backend API changes

Run `npm run codegen`. New hooks and types appear in `generated.ts` automatically.

### Adding custom endpoints

Create a file in `src/services/api/` using `baseApi.injectEndpoints()`. See `uploadApi.ts` and `projectsApi.ts` for examples. Add any new cache tag types to the `tagTypes` array in `baseApi.ts`.

### Adding hook wrappers

Create a file in `src/hooks/` that imports hooks from `@/services/api` and returns a flattened response shape. See `useProjects.ts` for the pattern.
