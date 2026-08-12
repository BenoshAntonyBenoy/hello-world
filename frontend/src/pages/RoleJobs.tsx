import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count, relativeDate, salaryLabel } from '@/lib/format'
import {
  Caveat,
  EmptyState,
  ErrorState,
  Page,
  RoleTabs,
  SampleDataBadge,
  Skeleton,
} from '@/components/ui'

const PAGE_SIZE = 12

export default function RoleJobs() {
  const { role = '' } = useParams()
  const [page, setPage] = useState(0)
  const { data, loading, error, notFound, reload } = useAsync(
    () => api.roleJobs(role, PAGE_SIZE, page * PAGE_SIZE),
    [role, page],
  )

  usePageMeta(data ? `${data.role.title} — the postings behind the analysis` : 'Postings')

  const pages = data ? Math.ceil(data.total / PAGE_SIZE) : 0

  return (
    <Page>
      <div>
        <p className="label">Underlying postings</p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
          {data?.role.title ?? role} — jobs
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          The individual postings behind the analysis. Every figure elsewhere on this role is
          computed from these.
        </p>
      </div>

      <div className="mt-6">
        <RoleTabs slug={role} active="jobs" />
      </div>

      {loading && (
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      )}

      {notFound && (
        <div className="mt-6">
          <EmptyState
            title={`No postings for “${role}”`}
            body="This role has not been analysed yet."
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
          <div className="mt-6">
            <Caveat>{data.note}</Caveat>
          </div>

          <p className="tnum mt-4 text-sm text-muted">
            {count(data.total)} postings · showing {data.offset + 1}–
            {Math.min(data.offset + data.limit, data.total)}
          </p>

          {data.items.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="No postings on this page" body="Try going back a page." />
            </div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {data.items.map((job) => {
                const salary = salaryLabel(job)
                return (
                  <article key={job.id} className="card flex flex-col gap-3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h2 className="truncate text-sm font-medium" title={job.title}>
                          {job.title}
                        </h2>
                        <p className="truncate text-xs text-muted">
                          {job.company ?? 'Company not stated'}
                          {job.location && ` · ${job.location}`}
                        </p>
                      </div>
                      {job.is_sample_data && <SampleDataBadge />}
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {job.experience && <span className="chip">{job.experience}</span>}
                      {job.employment_type && <span className="chip">{job.employment_type}</span>}
                      {job.education_level && <span className="chip">{job.education_level}</span>}
                      {salary && (
                        <span className="chip border-low/30 bg-low/10 text-low">{salary}</span>
                      )}
                    </div>

                    {job.key_skills.length > 0 && (
                      <div>
                        <p className="label mb-1.5">Key skills</p>
                        <div className="flex flex-wrap gap-1.5">
                          {job.key_skills.map((skill) => (
                            <span
                              key={skill}
                              className="chip border-brand/25 bg-brand-soft text-brand-ink"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-3 text-xs text-faint">
                      <span>
                        {job.source} · {relativeDate(job.posted_at)}
                      </span>
                      {job.url ? (
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="link font-medium"
                        >
                          View original ↗
                        </a>
                      ) : (
                        <span title="Sample postings have no external listing to link to">
                          No link
                        </span>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>
          )}

          {pages > 1 && (
            <div className="mt-6 flex items-center justify-between gap-3">
              <button
                type="button"
                className="btn-secondary"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                ← Previous
              </button>
              <span className="tnum text-sm text-muted">
                Page {page + 1} of {pages}
              </span>
              <button
                type="button"
                className="btn-secondary"
                disabled={page + 1 >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </Page>
  )
}
