import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: ['../..'],
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: '../../tests/dashboard_test/setup.ts',
    include: ['../../tests/dashboard_test/**/*.{test,spec}.{ts,tsx}'],
    css: false,
  },
})
