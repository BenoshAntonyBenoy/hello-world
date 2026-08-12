/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Override the API origin. Empty in dev, where Vite proxies /api. */
  readonly VITE_API_BASE?: string
  /** Proxy target used by the dev server (see vite.config.ts). */
  readonly VITE_API_TARGET?: string
  /** 'true' when the bundle reads frozen JSON instead of a live API. */
  readonly VITE_STATIC_DATA?: string
  /** Base path the site is served from ('/hello-world/' on a project page). */
  readonly VITE_BASE_PATH?: string
  /**
   * 'true' when a serverless analyser is reachable at /api/analyze-job even
   * though the rest of the site is static. Set on the Vercel deployment.
   */
  readonly VITE_ANALYZER?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
