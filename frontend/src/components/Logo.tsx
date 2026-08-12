import { Link } from 'react-router-dom'

/**
 * The mark: an engineer in a hard hat.
 *
 * Drawn as one silhouette of overlapping shapes rather than outlined detail,
 * because it renders at 28px in the header and anything finer turns to mush.
 * Motion is a slow idle bob plus a hat-tip on hover; both are switched off by
 * the reduced-motion rule in index.css.
 */
export function EngineerMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden focusable="false">
      <rect width="32" height="32" rx="8" className="fill-brand" />
      <g className="logo-figure" fill="rgb(var(--on-brand))">
        <path d="M6.5 29.5a9.5 7.8 0 0 1 19 0z" />
        <circle cx="16" cy="18" r="3.6" />
        <rect x="6.2" y="12.2" width="19.6" height="2.5" rx="1.25" />
        <path d="M9.4 12.2a6.6 6.6 0 0 1 13.2 0z" />
        <rect x="15" y="4.6" width="2" height="3.2" rx="1" />
      </g>
    </svg>
  )
}

export function Logo({ withWordmark = true }: { withWordmark?: boolean }) {
  return (
    <Link
      to="/"
      title="Home"
      aria-label="hello-world — go to the home page"
      className="logo group flex shrink-0 items-center gap-2.5 rounded-lg"
    >
      <EngineerMark className="h-8 w-8 shrink-0" />
      {/* The wordmark costs ~95px, which on a 375px screen is the difference
          between a usable search field and one showing "Searc". The mark alone
          still carries the brand and still goes home. */}
      {withWordmark && (
        <span className="hidden font-mono text-[0.95rem] font-semibold tracking-tight sm:inline">
          hello-world
        </span>
      )}
    </Link>
  )
}
