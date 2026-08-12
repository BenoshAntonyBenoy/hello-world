import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Confidence, Priority, SkillStat } from '@/lib/types'
import { COURSES } from '@/content/courses'
import { count, pct } from '@/lib/format'

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ')
}

/* ------------------------------------------------------------------ layout */

export function Page({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cx('mx-auto w-full max-w-6xl px-5 py-8 sm:px-6 lg:py-12', className)}>
      {children}
    </div>
  )
}

export function SectionHead({
  title,
  hint,
  action,
}: {
  title: string
  hint?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {hint && <p className="mt-1 max-w-2xl text-sm text-muted">{hint}</p>}
      </div>
      {action}
    </div>
  )
}

/* ------------------------------------------------------------------- state */

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cx(
        'relative overflow-hidden rounded-md bg-raised',
        'after:absolute after:inset-0 after:-translate-x-full after:animate-shimmer',
        'after:bg-gradient-to-r after:from-transparent after:via-black/[0.04] after:to-transparent',
        'dark:after:via-white/[0.05]',
        className,
      )}
    />
  )
}

export function LoadingBlock({ rows = 5, label }: { rows?: number; label?: string }) {
  return (
    <div className="card p-5" role="status" aria-live="polite">
      <span className="sr-only">{label ?? 'Loading'}</span>
      <Skeleton className="mb-5 h-5 w-44" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-4 w-32 shrink-0" />
            <Skeleton className="h-2.5 flex-1" />
            <Skeleton className="h-4 w-10 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="card p-8 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-high/10 text-high">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <p className="text-sm font-medium">Something went wrong</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-muted">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-4">
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string
  body: string
  action?: ReactNode
}) {
  return (
    <div className="card p-10 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-raised text-faint">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" strokeLinecap="round" />
        </svg>
      </div>
      <p className="text-sm font-medium">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-muted">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

/* ------------------------------------------------------------------- chips */

const CONFIDENCE_COPY: Record<Confidence, string> = {
  high: 'Large enough sample to rely on',
  medium: 'Moderate sample — directionally useful',
  low: 'Small sample — treat as a weak signal',
}

export function ConfidenceChip({ level }: { level: Confidence }) {
  const tone =
    level === 'high'
      ? 'text-low border-low/30 bg-low/10'
      : level === 'medium'
        ? 'text-medium border-medium/30 bg-medium/10'
        : 'text-faint border-line bg-raised'
  return (
    <span className={cx('chip', tone)} title={CONFIDENCE_COPY[level]}>
      {level} confidence
    </span>
  )
}

const PRIORITY_TONE: Record<Priority, string> = {
  high: 'bg-high',
  medium: 'bg-medium',
  low: 'bg-low',
}

export function PriorityDot({ priority }: { priority: Priority }) {
  return (
    <span
      className={cx('inline-block h-2 w-2 shrink-0 rounded-full', PRIORITY_TONE[priority])}
      aria-hidden
    />
  )
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  const label = { high: 'Must have', medium: 'Important', low: 'Good to have' }[priority]
  const tone = {
    high: 'border-high/30 bg-high/10 text-high',
    medium: 'border-medium/30 bg-medium/10 text-medium',
    low: 'border-line bg-raised text-muted',
  }[priority]
  return <span className={cx('chip', tone)}>{label}</span>
}

/* -------------------------------------------------------------------- data */

export function StatTile({
  label,
  value,
  hint,
}: {
  label: string
  value: ReactNode
  hint?: string
}) {
  return (
    <div className="card p-4">
      <p className="label">{label}</p>
      <p className="tnum mt-1.5 text-2xl font-semibold tracking-tight">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  )
}

/**
 * One skill's frequency, split into the share of postings that list it as
 * required versus merely preferred. Flattening those into a single number
 * would hide the difference between "you need this" and "nice if you have it".
 */
/** Free courses for one requirement, opened in a new tab. */
function CourseMenu({ slug, skillName }: { slug: string; skillName: string }) {
  const courses = COURSES[slug]
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onDown(event: MouseEvent) {
      if (!wrap.current?.contains(event.target as Node)) setOpen(false)
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  // No button at all rather than one that opens an empty list.
  if (!courses?.length) return null

  return (
    <div ref={wrap} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="btn-secondary whitespace-nowrap px-3 py-1.5 text-xs"
      >
        View courses
        <svg
          viewBox="0 0 24 24"
          className={cx('h-3.5 w-3.5 transition-transform', open && 'rotate-180')}
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full z-30 mt-1.5 w-[19rem] rounded-xl border border-line bg-surface p-1.5 shadow-lift">
          <p className="label px-2.5 pb-1 pt-1.5">Free courses · {skillName}</p>
          {courses.map((course) => (
            <a
              key={course.url + course.title}
              href={course.url}
              target="_blank"
              rel="noreferrer noopener"
              className="block rounded-lg px-2.5 py-2 transition-colors hover:bg-raised"
            >
              <span className="block text-sm leading-snug">{course.title}</span>
              <span className="block text-xs text-faint">{course.provider} ↗</span>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export function SkillBar({ stat, index = 0 }: { stat: SkillStat; index?: number }) {
  const required = Math.min(stat.required_pct, stat.frequency_pct)
  const preferred = Math.max(0, stat.frequency_pct - required)

  // The meter is capped at 15rem rather than filling the row, so the percentage
  // sits next to the name it describes instead of a screen-width away from it.
  // The space that frees up carries the courses button.
  return (
    <div className="group grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-2 py-2.5 sm:grid-cols-[13rem_minmax(0,15rem)_3rem_minmax(0,1fr)]">
      <div className="min-w-0 sm:pr-2">
        <p className="truncate text-sm font-medium" title={stat.skill.canonical}>
          {stat.skill.canonical}
        </p>
        <p className="truncate text-xs text-muted">
          {count(stat.jobs_mentioning)} of {count(stat.total_jobs)} postings
        </p>
      </div>

      <div className="order-1 col-span-2 sm:order-none sm:col-span-1">
        <div
          className="flex h-2 w-full overflow-hidden rounded-full bg-raised"
          role="img"
          aria-label={`${stat.skill.canonical}: ${pct(stat.frequency_pct)} of postings, ${pct(stat.required_pct)} as a hard requirement`}
        >
          <div
            className="h-full origin-left animate-grow rounded-l-full bg-brand"
            style={{ width: `${required}%`, animationDelay: `${Math.min(index, 12) * 28}ms` }}
          />
          <div
            className="h-full origin-left animate-grow bg-brand/35"
            style={{ width: `${preferred}%`, animationDelay: `${Math.min(index, 12) * 28}ms` }}
          />
        </div>
      </div>

      <p className="tnum text-right text-sm font-semibold">{pct(stat.frequency_pct)}</p>

      <div className="order-2 col-span-2 flex justify-start sm:order-none sm:col-span-1 sm:justify-end">
        <CourseMenu slug={stat.skill.slug} skillName={stat.skill.canonical} />
      </div>
    </div>
  )
}

export function BarLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-muted">
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-4 rounded-full bg-brand" /> Listed as required
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-4 rounded-full bg-brand/35" /> Listed as preferred
      </span>
    </div>
  )
}

/* ------------------------------------------------------------------ notices */

export function Caveat({ children }: { children: ReactNode }) {
  return (
    <div className="flex gap-2.5 rounded-lg border border-medium/25 bg-medium/[0.07] px-3.5 py-3 text-xs leading-relaxed text-muted">
      <svg viewBox="0 0 24 24" className="mt-px h-4 w-4 shrink-0 text-medium" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v5m0 3h.01" strokeLinecap="round" />
      </svg>
      <p>{children}</p>
    </div>
  )
}

export function SampleDataBadge() {
  return (
    <span className="chip border-medium/30 bg-medium/10 text-medium" title="Generated for development — not a real vacancy">
      Sample data
    </span>
  )
}

/* --------------------------------------------------------------------- nav */

/**
 * Everything a person can do with a role, in the words they would use.
 *
 * Trends and the skill gap used to sit in the global header even though both
 * are scoped to a single role — you cannot ask "am I ready?" without saying
 * ready for what. Moving them here means the question only ever appears once
 * the role is already chosen, and the header stops asking people to pick
 * between five nouns before they know what any of them contain.
 */
export function RoleTabs({ slug, active }: { slug: string; active: string }) {
  const tabs = [
    { key: 'overview', label: 'Overview', to: `/jobs/${slug}` },
    { key: 'roadmap', label: 'What to learn', to: `/jobs/${slug}/roadmap` },
    { key: 'gap', label: 'Am I ready?', to: `/skill-gap?role=${slug}` },
    { key: 'trends', label: "What's changing", to: `/trends?role=${slug}` },
    { key: 'skills', label: 'Every requirement', to: `/jobs/${slug}/skills` },
    { key: 'jobs', label: 'Real postings', to: `/jobs/${slug}/listings` },
  ]
  return (
    <nav className="-mb-px flex gap-1 overflow-x-auto border-b border-line" aria-label="Role sections">
      {tabs.map((tab) => (
        <Link
          key={tab.key}
          to={tab.to}
          aria-current={active === tab.key ? 'page' : undefined}
          className={cx(
            'whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors',
            active === tab.key
              ? 'border-brand text-ink'
              : 'border-transparent text-muted hover:border-line hover:text-ink',
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}
