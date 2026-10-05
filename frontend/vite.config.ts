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
    port: 5173,
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
  },
})