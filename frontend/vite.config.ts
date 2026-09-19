import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Proxy /api -> backend Django en desarrollo: así el frontend llama a rutas
// relativas ('/api/...') sin preocuparse por el puerto del backend. CORS
// también está configurado en el backend (django-cors-headers) por si se
// consume la API desde otro origen (ej. build de producción servido aparte).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
