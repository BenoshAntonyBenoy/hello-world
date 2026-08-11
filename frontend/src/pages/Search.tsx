import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, isStaticBuild } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { count } from '@/lib/format'
import { SearchBar } from '@/components/SearchBar'
import { EmptyState, ErrorState, Page, Skeleton, cx } from '@/components/ui'

export default function Search() {
  const [params] = useSearchParams()
  const query = params.get('q') ?? ''
  const { data, loading, error, reload } = useAsync(() => api.roles(), [])

  const grouped = useMemo(() => {
    const roles = data ?? []
    const filtered = query
      ? roles.filter(
          (r) =>
            r.title.toLowerCase().includes(query.toLowerCase()) ||
            r.category.toLowerCase().includes(query.toLowerCase()),
        )
      : roles

    const map = new Map<string, typeof filtered>()
    for (const role of filtered) {
      const list = map.get(role.category) ?? []
      list.push(role)
      map.set(role.category, list)
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [data, query])

  return (
    <Page>
      <div className="mx-auto max-w-3xl text-center">
        <h1 className="text-3xl font-semibold tracking-tight">What job are you preparing for?</h1>
        <p className="mt-2 text-sm text-muted">
          Pick a role to see the requirements employers actually list, how they are shifting,
          and what to learn first.
        </p>
        <div className="mt-6">
          <SearchBar autoFocus initialValue={query} />
        </div>
      </div>

      {loading && (
        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="h-[4.5rem]" />
          ))}
        </div>
      )}

      {error && (
        <div className="mt-10">
          <ErrorState message={error} onRetry={reload} />
        </div>
      )}

      {data && grouped.length === 0 && (
        <div className="mt-10">
          <EmptyState
            title={`No role matches “${query}”`}
            body={
              isStaticBuild
                ? 'This demo analyses 13 roles. Clear the search to see all of them.'
                : 'We analyse 13 roles today. If yours is not here, paste a job description and we will analyse that posting on its own.'
            }
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <Link to="/search" className="btn-secondary">
                  Clear search
                </Link>
                {!isStaticBuild && (
                  <Link to="/analyze" className="btn-primary">
                    Analyse a job description
                  </Link>
                )}
              </div>
            }
          />
        </div>
      )}

      {grouped.length > 0 && (
        <div className="mt-10 space-y-8">
          {grouped.map(([category, roles]) => (
            <section key={category}>
              <h2 className="label mb-3">{category}</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {roles.map((role) => (
                  <Link
                    key={role.slug}
                    to={`/jobs/${role.slug}`}
                    className={cx(
                      'card group p-4 transition-all duration-150',
                      'hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-lift',
                    )}
                  >
                    <p className="text-sm font-medium group-hover:text-brand-ink">
                      {role.title}
                    </p>
                    {role.summary && (
                      <p className="mt-1 line-clamp-2 text-xs text-muted">{role.summary}</p>
                    )}
                    <p className="tnum mt-2 text-xs text-faint">
                      {count(role.analyzed_jobs)} postings analysed
                    </p>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </Page>
  )
}
