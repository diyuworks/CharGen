import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import os from 'os'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  cacheDir: path.join(os.tmpdir(), 'ai-character-platform-vite-cache'),
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})

