// Configuração do Vite — "como o projeto roda"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],   // plugin oficial: entende .jsx
  server: {
    // proxy = "intermediário": o frontend pede /api/... e o Vite
    // repassa pro backend em :8000. Assim não tem problema de CORS
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // rewrite: tira o /api do começo antes de repassar
        // /api/atletas -> /atletas (o caminho real do backend)
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
