import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count } from '@/lib/format'
import {
  BarLegend,
  ConfidenceChip,
  EmptyState,
  ErrorState,
  LoadingBlock,
  Page,
  PriorityBadge,
  RoleTabs,
  SectionHead,
  SkillBar,
  Skeleton,
  cx,
} from '@/components/ui'

const FILTERS = [
  { key: 'all', label: 'All', min: 0 },
  { key: 'must', label: 'Must have', min: 55 },
  { key: 'important', label: 'Important', min: 30 },
] as const

export default function RoleSkills() {
  const { role = '' } = useParams()
  const [filter, setFilter] = useState<(typeof FILTERS)[number]['key']>('all')
  const { data, loading, error, notFound, reload } = useAsync(
    () => api.roleSkills(role),
    [role],
  )
  const summary = useAsync(() => api.role(role), [role])

  usePageMeta(
    summary.data ? `${summary.data.role.title} — every requirement` : 'Role requirements',
  )

  const min = FILTERS.find((f) => f.key === filter)?.min ?? 0
  const groups = (data ?? [])
    .map((group) => ({
      ...group,
      skills: group.skills.filter((s) => s.frequency_pct >= min),
    }))
    .filter((group) => group.skills.length > 0)

  const totalShown = groups.reduce((sum, g) => sum + g.skills.length, 0)

  return (
    <Page>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="label">Detailed breakdown</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
            {summary.data?.role.title ?? role} — skills
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Every requirement extracted from the analysed postings, grouped by category and
            ordered by how often it appears.
          </p>
        </div>
        <Link to={`/jobs/${role}/roadmap`} className="btn-primary shrink-0">
          Turn this into a plan
        </Link>
      </div>

      <div className="mt-6">
        <RoleTabs slug={role} active="skills" />
      </div>

      {loading && (
        <div className="mt-6 space-y-5">
          <Skeleton className="h-9 w-64" />
          <LoadingBlock rows={7} label="Loading requirements" />
        </div>
      )}

      {notFound && (
        <div className="mt-6">
          <EmptyState
            title={`No analysis for “${role}”`}
            body="This role has not been analysed. Browse the roles we cover, or paste a job description."
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

      {data && !loading && (
        <>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-1 rounded-lg border border-line bg-raised p-1">
              {FILTERS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setFilter(option.key)}
                  className={cx(
                    'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                    filter === option.key
                      ? 'bg-surface text-ink shadow-card'
                      : 'text-muted hover:text-ink',
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <p className="tnum text-xs text-muted">
              {count(totalShown)} requirements shown
              {summary.data && ` · ${count(summary.data.analyzed_jobs)} postings analysed`}
            </p>
          </div>

          {groups.length === 0 ? (
            <div className="mt-5">
              <EmptyState
                title="Nothing meets this threshold"
                body="No requirement appears in enough postings to clear the filter you selected. Try widening it."
              />
            </div>
          ) : (
            <div className="mt-5 space-y-6">
              {groups.map((group) => (
                <section key={group.label}>
                  <SectionHead
                    title={group.label}
                    action={
                      <span className="tnum text-xs text-faint">
                        {group.skills.length} items
                      </span>
                    }
                  />
                  <div className="card p-5">
                    <div className="divide-y divide-line">
                      {group.skills.map((stat, i) => (
                        <div key={stat.skill.slug}>
                          <SkillBar stat={stat} index={i} />
                          <div className="flex flex-wrap items-center gap-2 pb-2.5 sm:pl-0">
                            <PriorityBadge priority={stat.priority} />
                            <ConfidenceChip level={stat.confidence} />
                            {stat.preferred_pct > 0 && (
                              <span className="chip">
                                {stat.preferred_pct.toFixed(0)}% list it as preferred
                              </span>
                            )}
                            {stat.skill.description && (
                              <span className="text-xs text-faint">
                                {stat.skill.description}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 border-t border-line pt-4">
                      <BarLegend />
                    </div>
                  </div>
                </section>
              ))}
            </div>
          )}
        </>
      )}
    </Page>
  )
}
