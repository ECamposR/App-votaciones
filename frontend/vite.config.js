import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/setup': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/v': 'http://127.0.0.1:8000',
    },
  },
})
