import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { pathAlias } from './alias.config.mjs';

export default defineConfig(({ mode }) => ({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('md-'),
        },
      },
    }),
  ],
  server: {
    host: 'localhost',
  },
  resolve: {
    alias: pathAlias,
  },
  build: {
    // Output directory for production builds
    outDir: 'dist',
    // Clear the output directory before building
    emptyOutDir: true,
    // Generate source maps for debugging
    sourcemap: mode !== 'production',
  },
  // Only expose env vars with this prefix to the client
  envPrefix: 'VITE_',
}));
