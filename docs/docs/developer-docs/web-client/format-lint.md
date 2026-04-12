---
title: Formatting and Linting
sidebar_position: 4
---

# Formatting and Linting

The web-client enforces code quality with two tools: Prettier for formatting and ESLint 9 for linting. Both run on the same file set (`src/**/*.{ts,tsx,css}`), with `eslint-config-prettier` disabling all ESLint rules that conflict with Prettier's output.

## Overview

| Tool | Version | Role | Config File |
|------|---------|------|-------------|
| Prettier | 3.8+ | Code formatting (whitespace, quotes, semicolons) | `.prettierrc` |
| ESLint | 9.39+ | Static analysis (type errors, React hooks, restricted globals) | `eslint.config.js` |
| TypeScript | 5.9 | Type checking (`strict: true`, `noUnusedLocals`, `noUnusedParameters`) | `tsconfig.app.json` |

Two Make targets provide the primary interface:

- **`make lint`** — formats with Prettier, then lints with ESLint auto-fix. Use during local development.
- **`make lint-cicd`** — checks formatting and linting without modifying files. Exits non-zero on any violation. Used as a CI quality gate.

## Key Concepts

### Prettier Configuration

`.prettierrc` defines the formatting rules:

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

Notable choices: no semicolons, single quotes, and a 100-character line width.

`.prettierignore` excludes build output, dependencies, and auto-generated files:

```
dist
node_modules
package-lock.json
openapi-schema.json
src/services/api/generated.ts
```

### ESLint Configuration

`eslint.config.js` uses the ESLint 9 flat config format with `defineConfig()`. The configuration layers four rule sets:

1. **`@eslint/js` recommended** — core JavaScript rules
2. **`typescript-eslint` recommendedTypeChecked** — type-aware TypeScript rules using the project's tsconfig
3. **`eslint-plugin-react-hooks`** — enforces the Rules of Hooks
4. **`eslint-plugin-react-refresh`** — ensures components are compatible with Vite HMR
5. **`eslint-config-prettier`** — disables all formatting rules that conflict with Prettier (applied last)

Type-aware linting is enabled via `parserOptions.project`, which points at both `tsconfig.app.json` and `tsconfig.node.json`. This allows ESLint to use TypeScript's type information for rules like `@typescript-eslint/no-floating-promises`.

### Global Ignores

ESLint globally ignores `dist/` and `src/services/api/generated.ts`. The generated file is excluded because it is auto-produced by the codegen pipeline and does not conform to the project's style rules.

### Custom Rules

Two project-specific rule overrides exist:

**`react-hooks/incompatible-library: off`** — TanStack Table's `useReactTable()` returns functions that React Compiler cannot safely memoize. This warning is informational only. Disabling it reduces noise without affecting correctness.

**`no-restricted-globals: fetch`** — direct `fetch()` calls are banned. All API calls must go through RTK Query hooks from `@/services/api`. This prevents bypassing the centralized auth, error handling, and caching layer. The only exceptions are in `baseApi.ts` (the RTK Query base query) and SSE `EventSource` callbacks, which suppress the rule with an inline `// eslint-disable` comment.

### TypeScript Strict Mode

`tsconfig.app.json` enables several compile-time checks that complement ESLint:

| Option | Effect |
|--------|--------|
| `strict: true` | Enables all strict type-checking options |
| `noUnusedLocals: true` | Errors on unused local variables |
| `noUnusedParameters: true` | Errors on unused function parameters |
| `noFallthroughCasesInSwitch: true` | Errors on switch case fallthrough without explicit comment |
| `noUncheckedSideEffectImports: true` | Errors on side-effect imports without type checking |

Type checking runs during the build (`tsc --noEmit` is part of `npm run build`) but is not part of the `make lint` target.

## Usage

### Local Development

To format and lint all source files with auto-fix:

```bash
make lint
```

This runs Prettier first (to normalize formatting), then ESLint with `--fix` (to auto-correct lintable issues). The two-step order matters — Prettier must run before ESLint so that formatting changes do not trigger ESLint violations.

To format only, without linting:

```bash
npm run format
```

To check formatting without modifying files:

```bash
npm run format:check
```

### CI Pipeline

The CI quality gate runs:

```bash
make lint-cicd
```

This executes `npm run lint:cicd:junit`, which:

1. Runs ESLint without `--fix` and outputs results in JUnit XML format (`lint-eslint.xml`)
2. Runs `prettier --check` to verify formatting without modifying files

The target exits non-zero if any violation is found, failing the pipeline.

### Suppressing a Rule

To suppress a rule on a specific line, use an inline disable comment with a justification:

```typescript
// eslint-disable-next-line no-restricted-globals -- SSE EventSource requires raw fetch
return fetch(input, { ...init, headers })
```

Do not disable rules at the file level or in the ESLint config without a clear, documented reason.

### Key Files

| File | Role |
|------|------|
| `eslint.config.js` | ESLint flat config — rule sets, ignores, custom rules |
| `.prettierrc` | Prettier formatting options |
| `.prettierignore` | Files excluded from Prettier |
| `tsconfig.app.json` | TypeScript strict mode and compile-time checks |
| `Makefile` | `lint` and `lint-cicd` convenience targets |
