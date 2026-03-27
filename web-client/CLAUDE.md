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

## Key Conventions

- `routes.ts` uses `Component` (not `element`) so the route table stays in plain `.ts` with no JSX
- `lib/` has no React imports — code here could run in a service worker or Node script
- `layouts/` components are structural only — no data fetching
- `services/api/generated.ts` is auto-generated — never edit (see `services/api/README.md`)
- `config.ts` lives in `lib/` — it reads `window.__CONFIG__` set by `public/config.js`
