import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vitest/config';
import { pathAlias } from './alias.config.mjs';

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('md-'),
        },
      },
    }),
  ],
  resolve: {
    alias: pathAlias,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['tests/unit/setupTests.ts'],
    include: ['tests/unit/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['tests/e2e/**', 'node_modules', 'dist', 'playwright-report'],
    coverage: {
      reporter: ['text', 'html'],
      include: ['src/**/*.{js,jsx,ts,tsx,vue}'],
      exclude: ['src/main.js', 'tests/**'],
    },
  },
});
