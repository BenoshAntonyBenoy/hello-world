import { Link, useParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count } from '@/lib/format'
import {
  Caveat,
  ConfidenceChip,
  EmptyState,
  ErrorState,
  LoadingBlock,
  Page,
  PriorityDot,
  RoleTabs,
  Skeleton,
  cx,
} from '@/components/ui'

const STAGE_HINT: Record<string, string> = {
  Beginner: 'Foundations. Everything later depends on these.',
  Intermediate: 'Where most postings expect you to be working comfortably.',
  Advanced: 'Differentiators. Worth reaching once the base is solid.',
}

export default function RoleRoadmap() {
  const { role = '' } = useParams()
  // Passing the profile token lets the backend mark items the user already has.
  const { data, loading, error, notFound, reload } = useAsync(
    () => api.roleRoadmap(role, true),
    [role],
  )

  usePageMeta(
    data ? `Learning path for ${data.role.title}` : 'Learning path',
    data
      ? `What to learn for ${data.role.title}, ordered by demand with prerequisites scheduled first.`
      : undefined,
  )

  const known = data?.stages.flatMap((s) => s.items).filter((i) => i.already_known).length ?? 0
  const total = data?.stages.reduce((sum, s) => sum + s.items.length, 0) ?? 0

  return (
    <Page>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="label">Recommended learning path</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
            What should I learn for {data?.role.title ?? role}?
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Ordered by how often each skill appears in analysed postings, with prerequisites
            scheduled before the things that depend on them.
          </p>
        </div>
        <Link to="/skill-gap" className="btn-primary shrink-0">
          Compare with my skills
        </Link>
      </div>

      <div className="mt-6">
        <RoleTabs slug={role} active="roadmap" />
      </div>

      {loading && (
        <div className="mt-6">
          <LoadingBlock rows={8} label="Building roadmap" />
        </div>
      )}

      {notFound && (
        <div className="mt-6">
          <EmptyState
            title={`No roadmap for “${role}”`}
            body="We have not analysed this role yet, so there is no demand data to build a plan from."
            action={
              <Link to="/search" className="btn-primary">
                Browse roles
              </Link>
            }
          />
        </div>
      )}

      {error && !notFound && (
        <div className="mt-6">
          <ErrorState message={error} onRetry={reload} />
        </div>
      )}

      {data && !loading && data.stages.length === 0 && (
        <div className="mt-6">
          <EmptyState
            title="Not enough data for a roadmap"
            body="This role needs more analysed postings before we can order a meaningful learning path."
          />
        </div>
      )}

      {data && data.stages.length > 0 && (
        <>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <p className="tnum text-sm text-muted">
              {total} steps from {count(data.analyzed_jobs)} analysed postings
            </p>
            {known > 0 && (
              <span className="chip border-low/30 bg-low/10 text-low">
                {known} already in your profile
              </span>
            )}
          </div>

          <div className="mt-6 space-y-8">
            {data.stages.map((stage) => (
              <section key={stage.tier}>
                <div className="mb-3 flex items-baseline gap-3">
                  <h2 className="text-lg font-semibold tracking-tight">{stage.label}</h2>
                  <p className="text-sm text-muted">{STAGE_HINT[stage.label]}</p>
                </div>

                <ol className="card divide-y divide-line">
                  {stage.items.map((item) => (
                    <li
                      key={item.skill.slug}
                      className={cx(
                        'flex gap-4 p-4 transition-colors',
                        item.already_known && 'bg-low/[0.04]',
                      )}
                    >
                      <span
                        className={cx(
                          'tnum mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
                          item.already_known
                            ? 'bg-low/15 text-low'
                            : 'bg-raised text-muted',
                        )}
                      >
                        {item.already_known ? (
                          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                            <path d="m5 13 4 4L19 7" />
                          </svg>
                        ) : (
                          item.order
                        )}
                      </span>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-medium">{item.skill.canonical}</p>
                          <span className="flex items-center gap-1.5 text-2xs font-medium uppercase tracking-wide text-muted">
                            <PriorityDot priority={item.priority} />
                            {item.priority} priority
                          </span>
                          {item.already_known && (
                            <span className="chip border-low/30 bg-low/10 text-low">
                              You have this
                            </span>
                          )}
                        </div>

                        <p className="mt-1 text-sm text-muted">{item.reason}</p>

                        {item.prerequisites.length > 0 && (
                          <p className="mt-1.5 text-xs text-faint">
                            Build on: {item.prerequisites.join(', ')}
                          </p>
                        )}
                      </div>

                      <div className="hidden shrink-0 flex-col items-end gap-1.5 sm:flex">
                        <span className="tnum text-sm font-semibold">
                          {item.frequency_pct.toFixed(0)}%
                        </span>
                        <ConfidenceChip level={item.confidence} />
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
            ))}
          </div>

          <div className="mt-8">
            <Caveat>{data.note}</Caveat>
          </div>
        </>
      )}

      {!data && !loading && !error && !notFound && <Skeleton className="mt-6 h-64" />}
    </Page>
  )
}
