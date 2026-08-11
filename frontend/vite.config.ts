import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

/**
 * GitHub Pages has no server-side rewrite, so a deep link like
 * `/hello-world/jobs/data-analyst` is a 404 as far as it is concerned. Pages
 * serves `404.html` for anything it cannot find, so shipping a copy of the
 * app there lets React Router pick the route up from the unchanged URL.
 */
function spaFallback(): Plugin {
  return {
    name: 'spa-fallback-404',
    apply: 'build',
    closeBundle() {
      const dist = path.resolve(__dirname, 'dist')
      const index = path.join(dist, 'index.html')
      if (fs.existsSync(index)) {
        fs.copyFileSync(index, path.join(dist, '404.html'))
      }
    },
  }
}

// The API is proxied in development so the browser only ever talks to one
// origin. That keeps CORS out of the local setup entirely and means the
// production build can be served from the same host as the API unchanged.
export default defineConfig({
  // '/hello-world/' for a GitHub project page; '/' for local dev and for any
  // host serving the app at a domain root.
  base: process.env.VITE_BASE_PATH ?? '/',
  plugins: [react(), spaFallback()],
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
