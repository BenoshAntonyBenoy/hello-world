import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { useDebounced } from '@/lib/hooks'
import type { RoleSummary } from '@/lib/types'
import { count } from '@/lib/format'
import { cx } from './ui'

interface Props {
  size?: 'lg' | 'md'
  placeholder?: string
  autoFocus?: boolean
  initialValue?: string
}

export function SearchBar({
  size = 'md',
  placeholder = 'Search a job title…',
  autoFocus = false,
  initialValue = '',
}: Props) {
  const navigate = useNavigate()
  const listId = useId()
  const [query, setQuery] = useState(initialValue)
  const [results, setResults] = useState<RoleSummary[]>([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [searching, setSearching] = useState(false)
  const wrapper = useRef<HTMLDivElement>(null)

  const debounced = useDebounced(query, 200)

  useEffect(() => {
    const term = debounced.trim()
    if (term.length < 2) {
      setResults([])
      setSearching(false)
      return
    }
    let active = true
    setSearching(true)
    api
      .searchRoles(term)
      .then((rows) => {
        if (!active) return
        setResults(rows)
        setActive(rows.length ? 0 : -1)
      })
      .catch(() => active && setResults([]))
      .finally(() => active && setSearching(false))
    return () => {
      active = false
    }
  }, [debounced])

  // Close on outside click so the panel does not linger over the page.
  useEffect(() => {
    function onDown(event: MouseEvent) {
      if (!wrapper.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  function go(role: RoleSummary) {
    setOpen(false)
    setQuery(role.title)
    navigate(`/jobs/${role.slug}`)
  }

  function submit() {
    const chosen = results[active] ?? results[0]
    if (chosen) return go(chosen)
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setOpen(true)
      setActive((i) => Math.min(i + 1, results.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      submit()
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  const big = size === 'lg'
  const showPanel = open && query.trim().length >= 2

  return (
    <div ref={wrapper} className="relative w-full">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <svg
            viewBox="0 0 24 24"
            className={cx(
              'pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-faint',
              big ? 'h-5 w-5' : 'h-4 w-4',
            )}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" strokeLinecap="round" />
          </svg>

          <input
            type="search"
            value={query}
            autoFocus={autoFocus}
            placeholder={placeholder}
            aria-label="Search a job title"
            aria-expanded={showPanel}
            aria-controls={listId}
            aria-autocomplete="list"
            role="combobox"
            className={cx(
              'input',
              big ? 'py-3.5 pl-11 pr-4 text-base' : 'py-2.5 pl-10 pr-3',
            )}
            onChange={(e) => {
              setQuery(e.target.value)
              setOpen(true)
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
          />
        </div>

        <button
          type="button"
          onClick={submit}
          className={cx('btn-primary shrink-0', big && 'px-5 py-3.5 text-base')}
        >
          {big ? 'Analyse Job Requirements' : 'Search'}
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14m-6-6 6 6-6 6" />
          </svg>
        </button>
      </div>

      {showPanel && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-30 mt-2 max-h-80 w-full overflow-auto rounded-xl border border-line bg-surface p-1.5 shadow-lift"
        >
          {searching && !results.length && (
            <li className="px-3 py-2.5 text-sm text-muted">Searching…</li>
          )}

          {!searching && !results.length && (
            <li className="px-3 py-2.5 text-sm text-muted">
              No role matches “{query.trim()}”. We currently analyse 13 roles —{' '}
              <button
                type="button"
                className="link"
                onClick={() => {
                  setOpen(false)
                  navigate('/search')
                }}
              >
                browse all
              </button>
              .
            </li>
          )}

          {results.map((role, i) => (
            <li key={role.slug} role="option" aria-selected={i === active}>
              <button
                type="button"
                onMouseEnter={() => setActive(i)}
                onClick={() => go(role)}
                className={cx(
                  'flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
                  i === active ? 'bg-raised' : 'hover:bg-raised',
                )}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{role.title}</span>
                  <span className="block truncate text-xs text-muted">{role.category}</span>
                </span>
                <span className="tnum shrink-0 text-xs text-faint">
                  {count(role.analyzed_jobs)} analysed
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
