import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from './api'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  notFound: boolean
  reload: () => void
}

/**
 * Run an async fetcher and track loading / error / result.
 *
 * Guards against the two classic bugs: setting state after unmount, and a slow
 * earlier request overwriting a faster later one when the key changes.
 */
export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  enabled = true,
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [nonce, setNonce] = useState(0)
  const requestId = useRef(0)

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }

    const id = ++requestId.current
    let active = true
    setLoading(true)
    setError(null)
    setNotFound(false)

    fetcher()
      .then((result) => {
        if (!active || id !== requestId.current) return
        setData(result)
      })
      .catch((err: unknown) => {
        if (!active || id !== requestId.current) return
        setData(null)
        if (err instanceof ApiError && err.status === 404) setNotFound(true)
        setError(err instanceof Error ? err.message : 'Something went wrong.')
      })
      .finally(() => {
        if (!active || id !== requestId.current) return
        setLoading(false)
      })

    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce, enabled])

  return { data, loading, error, notFound, reload }
}

/** Delay a rapidly changing value — used for search-as-you-type. */
export function useDebounced<T>(value: T, ms = 220): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(timer)
  }, [value, ms])
  return debounced
}

const DEFAULT_TITLE = 'hello-world — Learn what the industry actually wants'
const DEFAULT_DESCRIPTION =
  'hello-world analyses job postings to show the skills employers actually ask for, ' +
  'so you can prepare for the job rather than the syllabus.'

/**
 * Give a route its own title and description.
 *
 * A single-page app keeps whatever the server sent unless something updates it,
 * so without this every one of the twelve routes shares one tab label, one
 * history entry name and one preview snippet. Pass `null` for the landing page
 * to get the unprefixed default.
 */
export function usePageMeta(title: string | null, description?: string) {
  useEffect(() => {
    document.title = title ? `${title} · hello-world` : DEFAULT_TITLE
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute('content', description ?? DEFAULT_DESCRIPTION)
  }, [title, description])
}

const THEME_KEY = 'helloworld.theme'

export function useTheme() {
  const [dark, setDark] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(THEME_KEY)
      if (stored) return stored === 'dark'
    } catch {
      /* storage unavailable */
    }
    return globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try {
      localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light')
    } catch {
      /* storage unavailable */
    }
  }, [dark])

  return { dark, toggle: () => setDark((d) => !d) }
}
