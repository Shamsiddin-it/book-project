import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const DJANGO = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Проксируем на Django, чтобы в разработке фронт и API жили на одном origin.
    // Так CORS вообще не участвует, а токен и куки ведут себя как в проде.
    proxy: {
      '/api': { target: DJANGO, changeOrigin: true },
      '/media': { target: DJANGO, changeOrigin: true },
      '/admin': { target: DJANGO, changeOrigin: true },
      '/swagger': { target: DJANGO, changeOrigin: true },
    },
  },
})
