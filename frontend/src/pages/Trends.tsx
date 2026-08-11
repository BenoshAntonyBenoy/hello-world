import { useSearchParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { DirectionChip, Sparkline, TrendChart } from '@/components/charts'
import {
  Caveat,
  EmptyState,
  ErrorState,
  LoadingBlock,
  Page,
  SectionHead,
  Skeleton,
} from '@/components/ui'
import type { Trend } from '@/lib/types'

function TrendRow({ trend }: { trend: Trend }) {
  const positive = trend.change_pct >= 0
  return (
    <li className="flex items-center gap-4 p-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-medium">{trend.skill.canonical}</p>
          <DirectionChip direction={trend.direction} />
        </div>
        <p className="tnum mt-1 text-xs text-muted">
          {trend.current_pct.toFixed(0)}% of postings ·{' '}
          <span className={positive ? 'font-medium text-low' : 'font-medium text-high'}>
            {positive ? '+' : ''}
            {trend.change_pct.toFixed(1)}pp
          </span>{' '}
          over {trend.months_observed} months
        </p>
      </div>
      <Sparkline trend={trend} />
    </li>
  )
}

export default function Trends() {
  const [params, setParams] = useSearchParams()
  const roleSlug = params.get('role') ?? 'ai-ml-engineer'

  const roles = useAsync(() => api.roles(), [])
  const trends = useAsync(() => api.roleTrends(roleSlug), [roleSlug])

  const highlight = [
    ...(trends.data?.emerging.slice(0, 3) ?? []),
    ...(trends.data?.declining.slice(0, 2) ?? []),
  ]

  return (
    <Page>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label">Job market trends</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
            How requirements are shifting
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Month-by-month share of postings mentioning each skill. Useful when you are
            deciding what to spend the next six months on.
          </p>
        </div>

        <label className="shrink-0">
          <span className="label mb-1.5 block">Role</span>
          <select
            className="input min-w-[15rem] cursor-pointer"
            value={roleSlug}
            onChange={(e) => setParams({ role: e.target.value })}
          >
            {(roles.data ?? []).map((role) => (
              <option key={role.slug} value={role.slug}>
                {role.title}
              </option>
            ))}
          </select>
        </label>
      </div>

      {trends.loading && (
        <div className="mt-8 space-y-5">
          <Skeleton className="h-72" />
          <LoadingBlock rows={4} label="Loading trends" />
        </div>
      )}

      {trends.error && !trends.notFound && (
        <div className="mt-8">
          <ErrorState message={trends.error} onRetry={trends.reload} />
        </div>
      )}

      {trends.data && !trends.loading && (
        <>
          {highlight.length > 0 ? (
            <section className="mt-8">
              <SectionHead
                title="Twelve-month history"
                hint="The biggest movers for this role, plotted against the share of postings that mention them."
              />
              <div className="card p-5">
                <TrendChart trends={highlight} />
              </div>
            </section>
          ) : (
            <div className="mt-8">
              <EmptyState
                title="No significant movement detected"
                body={trends.data.note}
              />
            </div>
          )}

          <div className="mt-8 grid gap-5 lg:grid-cols-2">
            <section>
              <SectionHead
                title="Emerging skills"
                hint="Rising faster than sampling noise can explain."
              />
              {trends.data.emerging.length === 0 ? (
                <div className="card p-5 text-sm text-muted">
                  Nothing is rising significantly for this role right now.
                </div>
              ) : (
                <ul className="card divide-y divide-line">
                  {trends.data.emerging.map((trend) => (
                    <TrendRow key={trend.skill.slug} trend={trend} />
                  ))}
                </ul>
              )}
            </section>

            <section>
              <SectionHead
                title="Declining skills"
                hint="Still worth knowing — falling demand is not zero demand."
              />
              {trends.data.declining.length === 0 ? (
                <div className="card p-5 text-sm text-muted">
                  Nothing is falling significantly for this role right now.
                </div>
              ) : (
                <ul className="card divide-y divide-line">
                  {trends.data.declining.map((trend) => (
                    <TrendRow key={trend.skill.slug} trend={trend} />
                  ))}
                </ul>
              )}
            </section>
          </div>

          {trends.data.stable.length > 0 && (
            <section className="mt-8">
              <SectionHead
                title="Stable and consistently requested"
                hint="Flat demand at a high level is the strongest signal there is — these are the safe bets."
              />
              <ul className="card grid divide-y divide-line sm:grid-cols-2 sm:divide-y-0">
                {trends.data.stable.slice(0, 8).map((trend) => (
                  <TrendRow key={trend.skill.slug} trend={trend} />
                ))}
              </ul>
            </section>
          )}

          <div className="mt-8">
            <Caveat>{trends.data.note}</Caveat>
          </div>
        </>
      )}
    </Page>
  )
}
