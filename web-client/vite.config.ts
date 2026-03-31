import { execSync } from 'child_process'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react-swc'
import { defineConfig } from 'vite'

function getVersion(subcommand: string): string {
  try {
    return execSync(`python3 scripts/util/version.py ${subcommand}`)
      .toString()
      .trim()
  } catch {
    return subcommand === 'sha' ? 'unknown' : '0.0.0'
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(getVersion('version')),
    __BUILD_VERSION__: JSON.stringify(getVersion('sha')),
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
