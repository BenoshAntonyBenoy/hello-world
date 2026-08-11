/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Override the API origin. Empty in dev, where Vite proxies /api. */
  readonly VITE_API_BASE?: string
  /** Proxy target used by the dev server (see vite.config.ts). */
  readonly VITE_API_TARGET?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
