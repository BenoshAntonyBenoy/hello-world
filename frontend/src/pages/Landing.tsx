import { Link } from 'react-router-dom'
import { SearchBar } from '@/components/SearchBar'
import { Page, Skeleton, cx } from '@/components/ui'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { count } from '@/lib/format'

const EXAMPLES = [
  'Software Engineer',
  'Data Scientist',
  'Cybersecurity Analyst',
  'Embedded Systems Engineer',
  'UI/UX Designer',
  'DevOps Engineer',
]

const STEPS = [
  {
    n: '01',
    title: 'Collect postings',
    body: 'Job descriptions arrive through a connector layer — official APIs, licensed datasets, public boards, or ones you paste in yourself.',
  },
  {
    n: '02',
    title: 'Extract requirements',
    body: 'Each posting is parsed section by section, so a hard requirement is told apart from a nice-to-have, and “ReactJS” and “React.js” are counted as one thing.',
  },
  {
    n: '03',
    title: 'Count what recurs',
    body: 'Duplicate reposts and off-topic listings are removed first, then every skill gets a frequency and a confidence rating based on sample size.',
  },
  {
    n: '04',
    title: 'Turn it into a plan',
    body: 'Demand data becomes an ordered learning path, with prerequisites scheduled before the skills that depend on them.',
  },
]

function slugify(title: string): string {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

export default function Landing() {
  const { data: health } = useAsync(() => api.health(), [])
  const { data: roles } = useAsync(() => api.roles(), [])

  const topRoles = (roles ?? []).slice().sort((a, b) => b.analyzed_jobs - a.analyzed_jobs)

  return (
    <>
      {/* Hero ---------------------------------------------------------- */}
      <section className="relative overflow-hidden border-b border-line">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35] dark:opacity-25"
          style={{
            backgroundImage:
              'radial-gradient(60rem 32rem at 50% -12rem, rgb(var(--brand) / 0.16), transparent 70%)',
          }}
          aria-hidden
        />
        <Page className="relative lg:py-20">
          <div className="mx-auto max-w-3xl text-center">
            <span className="chip mx-auto mb-6 w-fit">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              Job requirements intelligence
            </span>

            <h1 className="animate-fade-up text-balance text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl">
              Know what industry wants.
            </h1>

            <p className="mx-auto mt-5 max-w-2xl text-balance text-base leading-relaxed text-muted sm:text-lg">
              hello-world helps you discover the skills employers actually ask for — so you
              can prepare for the job, not just the syllabus.
            </p>

            <div className="mx-auto mt-8 max-w-2xl">
              <SearchBar size="lg" placeholder="Search a job title…" />
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
              <span className="text-xs text-faint">Try:</span>
              {EXAMPLES.map((example) => (
                <Link
                  key={example}
                  to={`/jobs/${slugify(example)}`}
                  className="chip transition-colors hover:border-brand/40 hover:bg-brand-soft hover:text-brand-ink"
                >
                  {example}
                </Link>
              ))}
            </div>

            {health && (
              <p className="tnum mt-8 text-xs text-faint">
                {count(health.analyzed_jobs)} postings analysed across {health.roles} roles ·{' '}
                {health.skills} requirements in the vocabulary
              </p>
            )}
          </div>
        </Page>
      </section>

      {/* The problem ---------------------------------------------------- */}
      <Page>
        <div className="grid gap-10 lg:grid-cols-[1fr_1.15fr] lg:gap-14">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              The syllabus moves slower than the market.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              A student who wants to become a Data Analyst has no reliable way to find out
              what a Data Analyst actually needed to learn. What they get instead is a
              syllabus written years ago, job descriptions listing fifteen tools without
              saying which three mattered, and roadmaps optimised for watch time.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              The information exists — it is sitting in the postings themselves. It just
              never reaches the person who needs it.
            </p>
            <Link to="/about" className="link mt-4 inline-block text-sm">
              How we read the data →
            </Link>
          </div>

          <div className="card divide-y divide-line">
            {STEPS.map((step) => (
              <div key={step.n} className="flex gap-4 p-5">
                <span className="tnum font-mono text-xs font-semibold text-brand">{step.n}</span>
                <div>
                  <p className="text-sm font-medium">{step.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted">{step.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Page>

      {/* Roles ---------------------------------------------------------- */}
      <Page className="pt-0">
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Roles we analyse</h2>
            <p className="mt-1 text-sm text-muted">
              Every role below has a full requirement breakdown, trend history and learning path.
            </p>
          </div>
          <Link to="/search" className="btn-secondary shrink-0">
            Browse all
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
                'hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-lift',
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
                {count(role.analyzed_jobs)} postings analysed · {role.category}
              </p>
            </Link>
          ))}
        </div>
      </Page>
    </>
  )
}
