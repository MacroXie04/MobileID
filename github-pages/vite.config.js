import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import fs from 'fs'
import path from 'path'
import { dirname } from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('md-')
        }
      }
    })
  ],
  server: { 
    host: "127.0.0.1",
    port: 5173,
    // Use custom certificates for better compatibility
    https: {
      key: fs.readFileSync(path.resolve(dirname(fileURLToPath(import.meta.url)), 'certificates/localhost-key.pem')),
      cert: fs.readFileSync(path.resolve(dirname(fileURLToPath(import.meta.url)), 'certificates/localhost.pem'))
    },
    
    // Handle self-signed certificate issues
    hmr: {
      port: 5173
    }
  },
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) }
  },
  // Additional HTTPS-related configuration
  preview: {
    https: true,
    host: "127.0.0.1",
    port: 4173
  }
});