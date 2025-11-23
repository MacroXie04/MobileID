import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
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
  },
});
