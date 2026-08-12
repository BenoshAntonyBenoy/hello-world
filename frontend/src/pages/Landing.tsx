import { Link } from 'react-router-dom'
import { SearchBar } from '@/components/SearchBar'
import { Page, Skeleton, cx } from '@/components/ui'
import { analyzerAvailable, api } from '@/lib/api'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count } from '@/lib/format'

const EXAMPLES = [
  'Software Engineer',
  'Data Analyst',
  'Cybersecurity Analyst',
  'UI/UX Designer',
  'Digital Marketing Specialist',
]

/** Three things a person can actually get here, named as outcomes. */
const OUTCOMES = [
  {
    title: 'See what employers ask for',
    body: 'The skills that came up most often across real postings for that job — and how many asked for each.',
    icon: (
      <path d="M4 19V9m5 10V5m5 14v-7m5 7V8" strokeLinecap="round" />
    ),
  },
  {
    title: 'Get a plan for what to learn',
    body: 'Those skills put in order, so you never start on something before the thing it depends on.',
    icon: (
      <path d="M5 6h14M5 12h9M5 18h5m5.5 1.5L18 22l4-5.5" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
  {
    title: 'Find out if you are ready',
    body: 'Tick off what you already know and see how much of the job you cover, and what to close first.',
    icon: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="m8.5 12 2.5 2.5 4.5-5" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
]

export default function Landing() {
  usePageMeta(null)
  const { data: health } = useAsync(() => api.health(), [])
  const { data: roles } = useAsync(() => api.roles(), [])

  const topRoles = (roles ?? []).slice().sort((a, b) => b.analyzed_jobs - a.analyzed_jobs)

  return (
    <>
      {/* Hero ----------------------------------------------------------- */}
      <section className="relative isolate overflow-hidden border-b border-line">
        <div
          className="hero-photo absolute inset-0 -z-20"
          style={{ backgroundImage: `url(${import.meta.env.BASE_URL}hero-studying.jpg)` }}
          aria-hidden
        />
        {/* The scrim, not the photograph, is what makes the headline legible —
            the image only has to survive behind it. Even over the darkest part
            of the photo this keeps body text above 9:1 in both themes. */}
        <div
          className="absolute inset-0 -z-10 bg-canvas/[0.76] dark:bg-canvas/[0.86]"
          aria-hidden
        />
        {/* Fades the photograph out into the page rather than ending it on a line. */}
        <div
          className="absolute inset-x-0 bottom-0 -z-10 h-28 bg-gradient-to-b from-transparent to-canvas"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          style={{
            backgroundImage:
              'radial-gradient(55rem 30rem at 50% -8rem, rgb(var(--brand) / 0.20), transparent 72%)',
          }}
          aria-hidden
        />

        <Page className="relative lg:py-24">
          <div className="mx-auto max-w-3xl text-center">
            <span className="chip mx-auto mb-6 w-fit border-brand/30 bg-brand-soft text-brand-ink">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              Built from real job postings
            </span>

            <h1 className="animate-fade-up text-balance text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.75rem]">
              What job do you want?
            </h1>

            <p className="mx-auto mt-5 max-w-xl text-balance text-base leading-relaxed text-muted sm:text-lg">
              Type it below. We will show you the skills employers actually ask for, in what
              order to learn them, and how far along you already are.
            </p>

            <div className="mx-auto mt-8 max-w-2xl">
              <SearchBar size="lg" autoFocus placeholder="e.g. Data Analyst" />
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
              <span className="text-xs text-faint">Popular:</span>
              {EXAMPLES.map((example) => (
                <Link
                  key={example}
                  to={`/jobs/${example.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                  // These chips are a primary way in, so they get a real tap
                  // target rather than the 26px the default chip padding gives.
                  className="chip bg-surface/80 px-3.5 py-2 text-xs transition-colors hover:border-brand/40 hover:bg-brand-soft hover:text-brand-ink"
                >
                  {example}
                </Link>
              ))}
            </div>

            {health && (
              <p className="tnum mt-8 text-xs text-faint">
                {count(health.analyzed_jobs)} postings read · {health.roles} jobs covered ·{' '}
                {health.skills} skills tracked
              </p>
            )}
          </div>
        </Page>
      </section>

      {/* What you get ---------------------------------------------------- */}
      <Page>
        <div className="grid gap-4 sm:grid-cols-3">
          {OUTCOMES.map((item) => (
            <div key={item.title} className="card p-5">
              <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-brand-soft text-brand-ink">
                <svg viewBox="0 0 24 24" className="h-[1.15rem] w-[1.15rem]" fill="none" stroke="currentColor" strokeWidth="1.9">
                  {item.icon}
                </svg>
              </span>
              <p className="font-medium">{item.title}</p>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </Page>

      {/* Jobs ------------------------------------------------------------ */}
      <Page className="pt-0">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Or pick a job to start from</h2>
            <p className="mt-1 text-sm text-muted">
              Every one below has a full breakdown, a learning plan and the postings behind it.
            </p>
          </div>
          <Link to="/search" className="btn-secondary shrink-0">
            See all {health?.roles ?? ''} jobs
          </Link>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {!roles &&
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="card p-4">
                <Skeleton className="h-4 w-36" />
                <Skeleton className="mt-2 h-3 w-24" />
              </div>
            ))}

          {topRoles.slice(0, 9).map((role, i) => (
            <Link
              key={role.slug}
              to={`/jobs/${role.slug}`}
              className={cx(
                'card group p-4 transition-all duration-150',
                'hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-lift',
              )}
              style={{ animationDelay: `${i * 25}ms` }}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium group-hover:text-brand-ink">{role.title}</p>
                <svg
                  viewBox="0 0 24 24"
                  className="mt-0.5 h-4 w-4 shrink-0 text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-brand"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 12h14m-6-6 6 6-6 6" />
                </svg>
              </div>
              <p className="tnum mt-1 text-xs text-muted">
                {count(role.analyzed_jobs)} postings read · {role.category}
              </p>
            </Link>
          ))}
        </div>
      </Page>

      {/* Job ad + honesty ------------------------------------------------ */}
      <Page className="pt-0">
        <div className="grid gap-4 lg:grid-cols-2">
          {analyzerAvailable && (
            <div className="card flex flex-col justify-between gap-4 p-6">
              <div>
                <h2 className="text-lg font-semibold tracking-tight">
                  Already have a job ad in front of you?
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  Paste it in and we will pull out exactly what it is asking for, then show you how
                  that compares with everything else on the market.
                </p>
              </div>
              <Link to="/analyze" className="btn-primary w-fit">
                Paste a job ad
              </Link>
            </div>
          )}

          <div className="card flex flex-col justify-between gap-4 p-6">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">
                Where these numbers come from
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                We read job postings and count what recurs. Every figure carries the number of
                postings behind it, so you can tell a strong signal from a small sample — and we
                say plainly what the numbers cannot tell you.
              </p>
            </div>
            <Link to="/about" className="btn-secondary w-fit">
              How this works
            </Link>
          </div>
        </div>
      </Page>
    </>
  )
}
