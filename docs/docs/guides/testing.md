---
title: Testing
sidebar_position: 7
---

# Testing

## Overview

This guide covers running and extending tests across the IPA project. Currently, the web client has a full Vitest unit test suite; the backend uses pytest.

## Web Client Unit Tests

The web client (`web-client/`) uses **Vitest 4** with **jsdom**, **React Testing Library**, and **MSW v2** for API mocking.

### Running Tests

From the `web-client/` directory:

```bash
npm test              # single run
npm run test:watch    # watch mode (re-runs on file changes)
npm run test:coverage # single run with coverage report
```

From the project root via Make:

```bash
make -f scripts/test.mk test          # all tests
make -f scripts/test.mk test-web      # web-client only
make -f scripts/test.mk test-web-cov  # web-client with coverage
```

### Test Structure

Tests are **co-located** next to their source files:

```
src/
├── lib/
│   ├── utils.ts
│   ├── utils.test.ts          ← test file next to source
│   ├── config.ts
│   └── config.test.ts
├── pages/
│   ├── LoginPage.tsx
│   ├── LoginPage.test.tsx
│   └── passengers/
│       ├── PassengersPage.tsx
│       └── PassengersPage.test.tsx
└── test/                      ← shared test infrastructure
    ├── setup.ts               # global setup (jest-dom, window.__CONFIG__, MSW)
    ├── test-utils.tsx          # renderWithProviders, createTestStore
    └── msw/
        ├── handlers.ts         # default API mock handlers
        └── server.ts           # MSW server instance
```

### Writing Tests

#### Pure utility functions

```ts
import { cn } from './utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })
})
```

#### Components with providers (Redux, Router, Feature Flags)

```tsx
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { MyPage } from './MyPage'

it('renders data from the API', async () => {
  renderWithProviders(<MyPage />)
  await waitFor(() => {
    expect(screen.getByText('Expected content')).toBeInTheDocument()
  })
})
```

`renderWithProviders` wraps the component in a Redux store, MemoryRouter, and FlagsProvider. It returns `{ ...render(), store, user }` where `user` is a `userEvent.setup()` instance for simulating interactions.

#### Testing hooks

```tsx
import { renderHook, waitFor } from '@testing-library/react'
import { createWrapper } from '@/test/test-utils'

const { result } = renderHook(() => useMyHook(), {
  wrapper: createWrapper(),
})
```

#### Overriding API responses per test

Default MSW handlers return success responses. Override for error scenarios:

```tsx
import { http, HttpResponse } from 'msw'
import { server } from '@/test/msw/server'

it('shows error when API fails', async () => {
  server.use(
    http.get('http://localhost/api/v1/endpoint', () => {
      return new HttpResponse(null, { status: 500 })
    }),
  )
  renderWithProviders(<MyPage />)
  await waitFor(() => {
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })
})
```

MSW handlers use absolute URLs (`http://localhost/api/v1/...`) matching the `API_BASE_URL` in the test setup.

### Adding Tests for a New Feature

When adding a new page or API endpoint:

1. **Add MSW handlers** in `src/test/msw/handlers.ts` for any new API routes
2. **Create a test file** next to the source (e.g., `NewPage.test.tsx` alongside `NewPage.tsx`)
3. **Test key behaviors**: renders heading, shows loading state, displays data, handles errors
4. **Run tests** to verify: `npm test`

### Coverage

Coverage reports are generated with `npm run test:coverage`. Reports are output in text (terminal), HTML (`coverage/index.html`), and lcov formats. No minimum threshold is enforced.

Coverage excludes test infrastructure, generated code, and third-party UI primitives.

## Backend Tests (app-lib)

The backend uses **pytest 8.3+** with **pytest-cov**. See the `app-lib/` directory for details.

```bash
cd app-lib
make test          # unit tests
make integration   # live service tests
make lint          # auto-fix linting
```
