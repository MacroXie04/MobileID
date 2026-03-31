import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { pathAlias } from './alias.config.mjs';

export default defineConfig(({ mode }) => ({
  base: process.env.VITE_BASE_PATH || '/',
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
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router'],
          'vendor-axios': ['axios'],
          'vendor-material': [
            '@material/web/button/filled-button.js',
            '@material/web/button/filled-tonal-button.js',
            '@material/web/button/outlined-button.js',
            '@material/web/button/text-button.js',
            '@material/web/chips/assist-chip.js',
            '@material/web/chips/filter-chip.js',
            '@material/web/dialog/dialog.js',
            '@material/web/divider/divider.js',
            '@material/web/icon/icon.js',
            '@material/web/iconbutton/icon-button.js',
            '@material/web/list/list.js',
            '@material/web/list/list-item.js',
            '@material/web/progress/circular-progress.js',
            '@material/web/progress/linear-progress.js',
            '@material/web/select/outlined-select.js',
            '@material/web/select/select-option.js',
            '@material/web/switch/switch.js',
            '@material/web/textfield/outlined-text-field.js',
          ],
          'vendor-cropper': ['cropperjs'],
        },
      },
    },
  },
  // Only expose env vars with this prefix to the client
  envPrefix: 'VITE_',
}));
