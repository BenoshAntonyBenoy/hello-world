import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// The API is proxied in development so the browser only ever talks to one
// origin. That keeps CORS out of the local setup entirely and means the
// production build can be served from the same host as the API unchanged.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  build: {
    rollupOptions: {
      output: {
        // Recharts is roughly two thirds of the bundle and is only needed on
        // the trends and dashboard views. Splitting it keeps the landing page,
        // which is where most first visits land, small.
        manualChunks: {
          charts: ['recharts'],
          react: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
  server: {
    port: 5190,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET ?? 'http://localhost:8010',
        changeOrigin: true,
      },
    },
  },
})
