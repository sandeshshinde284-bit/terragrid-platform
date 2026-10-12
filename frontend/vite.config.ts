import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
      '@components': path.resolve(import.meta.dirname, './src/components'),
      '@stores': path.resolve(import.meta.dirname, './src/stores'),
      '@composables': path.resolve(import.meta.dirname, './src/composables'),
      '@services': path.resolve(import.meta.dirname, './src/services'),
      '@utils': path.resolve(import.meta.dirname, './src/utils'),
      '@types': path.resolve(import.meta.dirname, './src/types'),
    },
  },
  server: {
    port: 5174,
    strictPort: false,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
  build: {
    target: 'es2017',
    sourcemap: false,
    // mapbox-gl builds its tile-loading worker by stringifying its own
    // source and re-executing it in a Worker from a Blob URL. esbuild's
    // minifier (Vite's default) renames local variables and breaks that
    // re-execution, causing "ReferenceError: <x> is not defined" inside
    // mapbox-gl's minified internals (e.g. Pe.loadTile) at tile-load time
    // in production only (dev mode skips minification, so this never
    // shows up locally). terser does not have this bug.
    minify: 'terser',

  },
  define: {
    'process.env': {}
  },
  optimizeDeps: {
    exclude: ['mapbox-gl']
  }
})
