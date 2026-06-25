# web-client

Guidance for AI coding assistants working in the web-client.

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

## Placement Rules

When adding a new file, follow this decision tree:

1. Is it a route-level view? → `pages/`
2. Is it a structural shell with `<Outlet />`? → `layouts/`
3. Is it a shared UI component? → `components/` (or `components/ui/` if shadcn)
4. Is it a shared React hook? → `hooks/`
5. Is it a framework-agnostic utility? → `lib/`
6. Is it an API endpoint? → `services/api/`
7. Is it Redux state/middleware? → `store/`
8. Is it auth-related? → `auth/`
9. Is it a React context provider? → `providers/`

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Directories | kebab-case | `data-table/`, `services/api/` |
| React components | PascalCase `.tsx` | `PassengersPage.tsx`, `RootLayout.tsx` |
| Hooks | camelCase with `use` prefix `.ts` | `useProjects.ts` |
| Utilities / config | camelCase `.ts` | `config.ts`, `setupLogging.ts` |
| Barrel exports | `index.ts` | `services/api/index.ts` |

## Adding a Page

1. Create a `.tsx` file in `src/pages/`
2. Add a route object to `src/routes.ts`
3. Optionally add a `<Link>` in the layout or another page

## Feature Escape Hatch

When a domain grows to 3+ components with its own hooks and types, extract it into `src/features/<name>/` with its own `components/`, `hooks/`, and `index.ts` public API. Features must not import from other features — compose at the page/route level.

## Testing

Unit tests use **Vitest 4** with **jsdom**, **React Testing Library**, and **MSW v2** for API mocking.

### Running Tests

```bash
cd web-client
npm test              # single run
npm run test:watch    # watch mode
npm run test:coverage # with coverage report
```

Or from the project root:

```bash
make -f scripts/test.mk test-web
```

### Test Infrastructure

```
src/mocks/
├── handlers.ts        # Shared MSW request handlers (relative URLs) — used by tests AND dev
├── browser.ts         # setupWorker(...handlers) — browser worker for mock-UX mode
├── AGENTS.md          # Terse do/don't for handler authoring
└── README.md          # The three-stage UX-first loop + mock→real recipe
src/test/
├── setup.ts           # Global setup: jest-dom, window.__CONFIG__, matchMedia mock, MSW lifecycle
├── test-utils.tsx     # renderWithProviders(), createTestStore(), createWrapper()
└── msw/
    └── server.ts      # MSW setupServer instance (imports handlers from src/mocks/)
```

- **`setup.ts`** sets `window.__CONFIG__` with `API_BASE_URL: 'http://localhost'` and auth disabled (empty OIDC values). MSW server starts before all tests, resets handlers after each, and closes after all.
- **`test-utils.tsx`** provides `renderWithProviders(ui, options?)` which wraps components in Redux store + FlagsProvider + MemoryRouter. Returns `{ ...render(), store, user }` where `user` is a `userEvent.setup()` instance.

### Writing a New Test

1. Create `ComponentName.test.tsx` (or `util.test.ts`) **next to** the source file
2. Import from `@/test/test-utils` for component tests needing providers:
   ```tsx
   import { screen, waitFor } from '@testing-library/react'
   import { renderWithProviders } from '@/test/test-utils'
   ```
3. For components that fetch data via RTK Query, MSW handlers in `src/test/msw/handlers.ts` provide default responses. Override per-test with `server.use()`:
   ```tsx
   import { http, HttpResponse } from 'msw'
   import { server } from '@/test/msw/server'

   server.use(
     http.get('http://localhost/api/v1/endpoint', () => {
       return new HttpResponse(null, { status: 500 })
     }),
   )
   ```
4. For pure UI components (no data fetching/providers), use plain `render()` from `@testing-library/react`
5. For hooks, use `renderHook()` with `createWrapper()`:
   ```tsx
   import { renderHook, waitFor } from '@testing-library/react'
   import { createWrapper } from '@/test/test-utils'

   const { result } = renderHook(() => useMyHook(), { wrapper: createWrapper() })
   ```

### When Adding a New API Endpoint

1. Add an MSW handler in `src/mocks/handlers.ts` using **relative** URLs (`/api/v1/...`). This one set is shared by the Node test server (`src/test/msw/server.ts`) and the browser worker (`src/mocks/browser.ts`), so the same mock serves both tests and mock-UX mode.
2. Write tests for any page/hook that consumes the new endpoint. Per-test overrides via `server.use(...)` may use absolute `http://localhost/api/v1/...` URLs — the test origin is pinned to that host.

### What NOT to Test

- `src/components/ui/` — shadcn/ui generated primitives (third-party code)
- `src/services/api/generated.ts` — auto-generated by codegen
- SSE/EventSource streaming — deferred to future phase

### Coverage

Coverage reports (text, HTML, lcov) are generated with `npm run test:coverage`. No minimum threshold enforced. Coverage excludes: `src/test/`, `src/services/api/generated.ts`, `src/components/ui/`, `src/vite-env.d.ts`.

## Key Conventions

- `routes.ts` uses `Component` (not `element`) so the route table stays in plain `.ts` with no JSX
- `lib/` has no React imports — code here could run in a service worker or Node script
- `layouts/` components are structural only — no data fetching
- `services/api/generated.ts` is auto-generated — never edit (see `services/api/README.md`)
- `config.ts` lives in `lib/` — it reads `window.__CONFIG__` set by `public/config.js`

## Mock-UX Mode

UX-first development: build and iterate on screens against mocked API responses
before any backend exists, then scaffold the real backend *from* the mocks.

**Detect the mode with `config.MOCK_API === true`** (the single source of truth). When
true and the build is non-production, `main.tsx` starts the MSW browser worker
(`src/mocks/browser.ts`) so every `/api/v1/*` call is served from
`src/mocks/handlers.ts` with no backend on `:8000`.

Two **independent** switches:

| Switch | Controls | Type |
|---|---|---|
| `MOCK_API` | Data source: MSW vs real backend | top-level config key |
| `features.<name>` | UI visibility of a feature | `features.*` flag |

`MOCK_API` is a data-source switch, not a product feature — keep it top-level, never
under `features`. It defaults `false` everywhere; `infra/scripts/configure_frontend.py`
always writes `false`, and an `import.meta.env.PROD` guard refuses to start the worker
in a prod build, so mocking can never ship enabled.

**Stage-2 rule (the one to follow while building):** when you add or change a page
that fetches data, author/maintain its handler in `src/mocks/handlers.ts` in the same
change, returning JSON in the shape the real DTO will return. Gate in-progress features
behind a `features.*` flag so they ship dark. The handler is the API contract.

**Stage-3 (migrate to real):** turn a handler into an `app-lib` feature whose
`routes/{name}_dto.py` Pydantic shape mirrors the handler JSON, run the backend, then
`npm run codegen` re-types `services/api/generated.ts`, and flip `MOCK_API` off. See
`src/mocks/README.md` and `docs/.../developer-docs/web-client/ux-first-mocking.md`.
