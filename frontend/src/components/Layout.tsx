import type { ReactNode } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useTheme } from '@/lib/hooks'
import { isStaticBuild } from '@/lib/api'
import { Logo } from './Logo'
import { SearchBar } from './SearchBar'
import { cx } from './ui'

// There is no API server behind a static build, so point at the source instead
// of a /api/docs URL that would 404.
export const DOCS_LINK = isStaticBuild
  ? { href: 'https://github.com/BenoshAntonyBenoy/hello-world', label: 'Source on GitHub' }
  : { href: '/api/docs', label: 'API docs' }

function ThemeToggle() {
  const { dark, toggle } = useTheme()
  return (
    <button
      type="button"
      onClick={toggle}
      className="flex h-10 w-10 items-center justify-center rounded-lg text-muted transition-colors hover:bg-raised hover:text-ink"
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={dark ? 'Light theme' : 'Dark theme'}
    >
      {dark ? (
        <svg viewBox="0 0 24 24" className="h-[1.15rem] w-[1.15rem]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="h-[1.15rem] w-[1.15rem]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
        </svg>
      )}
    </button>
  )
}

function ProfileButton() {
  return (
    <NavLink
      to="/profile"
      title="Your profile"
      aria-label="Your profile"
      className={({ isActive }) =>
        cx(
          'flex h-10 w-10 items-center justify-center rounded-full border transition-colors',
          isActive
            ? 'border-brand/40 bg-brand-soft text-brand-ink'
            : 'border-line text-muted hover:bg-raised hover:text-ink',
        )
      }
    >
      <svg viewBox="0 0 24 24" className="h-[1.15rem] w-[1.15rem]" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="3.75" />
        <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
      </svg>
    </NavLink>
  )
}

/**
 * The header carries three things and nothing else: where you are (the mark,
 * which is also the way home), how you get anywhere (search), and you (the
 * profile). The old bar listed five destinations — Roles, Trends, Analyse a JD,
 * Skill gap, Profile — which asked a first-time visitor to know the difference
 * between them before they had seen a single number. Everything those pages do
 * is scoped to one role, so they now live as plain-language tabs inside that
 * role instead of as choices at the front door.
 */
export function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  const onLanding = pathname === '/'

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:text-sm focus:text-on-brand"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-20 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-3 px-4 sm:gap-4 sm:px-6">
          <Logo />

          {!onLanding && (
            <Link
              to="/"
              className="hidden items-center gap-1.5 rounded-lg px-2.5 py-2 text-sm font-medium text-muted transition-colors hover:bg-raised hover:text-ink sm:inline-flex"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 10.5 12 3l9 7.5M5.5 9.5V20h13V9.5" />
              </svg>
              Home
            </Link>
          )}

          {/* The landing page puts a full-size search in the hero, so repeating
              it here would be two of the same control on one screen. */}
          {!onLanding && (
            <div className="min-w-0 flex-1">
              <SearchBar compact placeholder="Search a job title…" />
            </div>
          )}

          <div className={cx('flex shrink-0 items-center gap-1.5', onLanding && 'ml-auto')}>
            <ThemeToggle />
            <ProfileButton />
          </div>
        </div>
      </header>

      <main id="main" className="flex-1">
        {children}
      </main>

      <footer className="mt-16 border-t border-line">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-5 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="font-mono text-xs font-semibold text-ink">hello-world</p>
            <p className="mt-1 text-xs">Learn what the industry actually wants.</p>
          </div>
          <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs">
            <Link to="/" className="hover:text-ink">
              Home
            </Link>
            <Link to="/search" className="hover:text-ink">
              All jobs
            </Link>
            <Link to="/analyze" className="hover:text-ink">
              Paste a job ad
            </Link>
            <Link to="/about" className="hover:text-ink">
              How this works
            </Link>
            <Link to="/profile" className="hover:text-ink">
              Your data
            </Link>
            <a
              href={DOCS_LINK.href}
              className="hover:text-ink"
              target="_blank"
              rel="noreferrer noopener"
            >
              {DOCS_LINK.label}
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
