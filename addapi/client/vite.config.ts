import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://34.133.163.39/addapi',
        // target: 'http://localhost:8080',
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    }
  },
  build: {
    outDir: '../addapi-build',
    emptyOutDir: true,
  },
  base: '/addapi/'
})
