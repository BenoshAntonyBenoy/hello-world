import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// Self-hosted so the type system the design was built for actually arrives:
// the sans stack names Inter and index.css sets Inter-only character variants,
// neither of which does anything unless the face is shipped. Bundled rather
// than fetched from a CDN so the static build works offline and adds no
// third-party request.
import '@fontsource-variable/inter'
import App from './App'
import './index.css'

// Vite injects the configured `base`. On a GitHub project page that is
// '/hello-world/', and every route has to be resolved relative to it.
const basename = import.meta.env.BASE_URL.replace(/\/$/, '')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename={basename}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
