import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import eslintConfigPrettier from 'eslint-config-prettier'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'src/services/api/generated.ts']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommendedTypeChecked,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        project: ['./tsconfig.app.json', './tsconfig.node.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // TanStack Table's useReactTable() returns functions that can't be memoized safely.
      // React Compiler automatically skips memoization for these components, which is correct.
      // This warning is informational only - disable to reduce noise.
      'react-hooks/incompatible-library': 'off',
      'no-restricted-globals': [
        'error',
        {
          name: 'fetch',
          message:
            'Use RTK Query hooks from @/services/api instead of fetch(). See docs/docs/solution/web-client/FORMAT-LINT.md',
        },
      ],
    },
  },
  eslintConfigPrettier,
])
