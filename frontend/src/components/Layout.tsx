import type { ReactNode } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useTheme } from '@/lib/hooks'
import { cx } from './ui'

const NAV = [
  { to: '/search', label: 'Roles' },
  { to: '/trends', label: 'Trends' },
  { to: '/analyze', label: 'Analyse a JD' },
  { to: '/skill-gap', label: 'Skill gap' },
  { to: '/profile', label: 'Profile' },
]

function Logo() {
  return (
    <Link to="/" className="flex shrink-0 items-center gap-2.5" aria-label="hello-world home">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand font-mono text-xs font-bold text-white">
        &gt;_
      </span>
      <span className="font-mono text-[0.95rem] font-semibold tracking-tight">hello-world</span>
    </Link>
  )
}

function ThemeToggle() {
  const { dark, toggle } = useTheme()
  return (
    <button
      type="button"
      onClick={toggle}
      className="rounded-lg p-2 text-muted transition-colors hover:bg-raised hover:text-ink"
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={dark ? 'Light theme' : 'Dark theme'}
    >
      {dark ? (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
        </svg>
      )}
    </button>
  )
}

export function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:text-sm focus:text-white"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-20 border-b border-line bg-canvas/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-4 px-5 sm:px-6">
          <Logo />

          <nav className="ml-2 hidden flex-1 items-center gap-0.5 md:flex" aria-label="Main">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cx(
                    'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive || pathname.startsWith(item.to)
                      ? 'bg-raised text-ink'
                      : 'text-muted hover:bg-raised hover:text-ink',
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Link to="/about" className="btn-ghost hidden px-3 py-1.5 sm:inline-flex">
              About
            </Link>
          </div>
        </div>

        {/* Mobile nav — the desktop bar collapses rather than hiding behind a
            menu button, since there are only five destinations. */}
        <nav
          className="flex gap-0.5 overflow-x-auto border-t border-line px-3 py-1.5 md:hidden"
          aria-label="Main (compact)"
        >
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cx(
                  'whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                  isActive ? 'bg-raised text-ink' : 'text-muted',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
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
            <Link to="/about" className="hover:text-ink">
              About &amp; data sources
            </Link>
            <Link to="/profile" className="hover:text-ink">
              Your data
            </Link>
            <a href="/api/docs" className="hover:text-ink" target="_blank" rel="noreferrer">
              API docs
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
