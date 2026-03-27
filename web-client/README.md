# web-client

A Vite + React 19 + TypeScript web application that uses RTK Query with OpenAPI codegen to auto-generate a typed API client from a FastAPI backend.

## Prerequisites

- Node.js 22+
- The FastAPI backend running on port 8000:

```bash
cd app-lib
pip install -e ".[rest]"
cd src/app_lib/rest
make run
```

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

## Format & Lint

The project uses Prettier for formatting and ESLint with type-aware rules for linting.

- `make lint` — Run during development. Formats all files with Prettier, then runs ESLint with `--fix`.
- `make lint-cicd` — Run in CI. Checks formatting and lint without modifying files. Exits non-zero on violations.

VS Code users: install `dbaeumer.vscode-eslint` and `rvest.vs-code-prettier-eslint`, then copy `.vscode/settings.json.example` to `.vscode/settings.json` for format-on-save.

## Codegen Pipeline

Running `npm run codegen` performs two steps:

1. Downloads the OpenAPI spec from `http://localhost:8000/openapi.json` into `openapi-schema.json`
2. Runs `@rtk-query/codegen-openapi` using `openapi-config.cjs` to produce `src/services/api/generated.ts`

The generated file contains typed endpoints, React hooks, and TypeScript types for every route in the FastAPI app.

> [!CAUTION]
> Do not edit `generated.ts` manually. It is overwritten on every codegen run.

The codegen config must be `.cjs` (CommonJS) because the `@rtk-query/codegen-openapi` CLI does not support ESM.

## Directory Layout

```
src/
├── auth/           # OIDC auth module (config + provider)
├── components/     # Shared UI components (components/ui/ for shadcn primitives)
├── hooks/          # Shared React hooks
├── layouts/        # Structural shells with <Outlet /> for react-router
├── lib/            # Framework-agnostic utilities (config, logging)
├── pages/          # Route-level page components (one per route)
├── providers/      # React context providers (Redux, future auth)
├── services/api/   # RTK Query base API, generated code, custom endpoints
├── store/          # Redux store, typed hooks, error middleware
├── main.tsx        # Entry point
└── routes.ts       # Route table (plain .ts, RouteObject[])
```

See `AGENTS.md` for placement rules and conventions. See `src/services/api/README.md` for RTK Query architecture details.

## Extending

### When the backend API changes

Run `npm run codegen`. New hooks and types appear in `generated.ts` automatically.

### Adding custom endpoints

Create a file in `src/services/api/` using `baseApi.injectEndpoints()`. See `uploadApi.ts` and `projectsApi.ts` for examples. Add any new cache tag types to the `tagTypes` array in `baseApi.ts`.

### Adding hook wrappers

Create a file in `src/hooks/` that imports hooks from `@/services/api` and returns a flattened response shape. See `useProjects.ts` for the pattern.
