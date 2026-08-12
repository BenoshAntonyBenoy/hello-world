import { Link, useParams } from 'react-router-dom'
import { api, isStaticBuild } from '@/lib/api'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count, dateLabel } from '@/lib/format'
import { DistributionBars, Sparkline, DirectionChip } from '@/components/charts'
import {
  BarLegend,
  Caveat,
  ConfidenceChip,
  EmptyState,
  ErrorState,
  LoadingBlock,
  Page,
  RoleTabs,
  SectionHead,
  SkillBar,
  Skeleton,
  StatTile,
} from '@/components/ui'

export default function RoleDashboard() {
  const { role = '' } = useParams()
  const analysis = useAsync(() => api.role(role), [role])
  const trends = useAsync(() => api.roleTrends(role), [role])

  const title = analysis.data?.role.title
  usePageMeta(
    title ? `${title} — what employers ask for` : 'Role requirements',
    title
      ? `The requirements most often listed in analysed ${title} postings, with sample sizes and confidence.`
      : undefined,
  )

  if (analysis.loading) {
    return (
      <Page>
        <Skeleton className="h-9 w-72" />
        <Skeleton className="mt-3 h-4 w-96" />
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="mt-8">
          <LoadingBlock rows={8} label="Loading skill analysis" />
        </div>
      </Page>
    )
  }

  if (analysis.notFound) {
    return (
      <Page>
        <EmptyState
          title={`We have not analysed “${role}” yet`}
          body={
            isStaticBuild
              ? 'This demo covers the roles listed below. Browse them to see the full requirement breakdown for each.'
              : 'We currently cover 13 roles. Browse the full list, or paste a job description and we will analyse that single posting instead.'
          }
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <Link to="/search" className="btn-primary">
                Browse roles
              </Link>
              {!isStaticBuild && (
                <Link to="/analyze" className="btn-secondary">
                  Analyse a job description
                </Link>
              )}
            </div>
          }
        />
      </Page>
    )
  }

  if (analysis.error || !analysis.data) {
    return (
      <Page>
        <ErrorState message={analysis.error ?? 'No data returned.'} onRetry={analysis.reload} />
      </Page>
    )
  }

  const data = analysis.data
  const emerging = trends.data?.emerging.slice(0, 4) ?? []

  return (
    <Page>
      {/* Header ------------------------------------------------------- */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="label">{data.role.category}</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">{data.role.title}</h1>
          {data.role.summary && (
            <p className="mt-2 max-w-2xl text-sm text-muted">{data.role.summary}</p>
          )}
        </div>
        <div className="flex shrink-0 gap-2">
          <Link to={`/jobs/${data.role.slug}/roadmap`} className="btn-primary">
            What should I learn?
          </Link>
          <Link to="/skill-gap" className="btn-secondary">
            Check my gap
          </Link>
        </div>
      </div>

      <div className="mt-6">
        <RoleTabs slug={data.role.slug} active="overview" />
      </div>

      {/* Stats -------------------------------------------------------- */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Postings analysed"
          value={count(data.analyzed_jobs)}
          hint={`${count(data.total_ingested)} collected before filtering`}
        />
        <StatTile
          label="Duplicates removed"
          value={count(data.duplicates_removed)}
          hint="Reposts and relists, excluded from every figure"
        />
        <StatTile
          label="Off-topic filtered"
          value={count(data.filtered_irrelevant)}
          hint="Listings that did not match the role"
        />
        <StatTile
          label="Most recent posting"
          value={<span className="text-lg">{dateLabel(data.last_updated)}</span>}
          hint={
            data.window_start
              ? `Window opens ${dateLabel(data.window_start)}`
              : 'No date range available'
          }
        />
      </div>

      <div className="mt-4">
        <Caveat>{data.data_caveat}</Caveat>
      </div>

      {/* Top skills ---------------------------------------------------- */}
      <section className="mt-10">
        <SectionHead
          title="Most requested skills"
          hint="Share of analysed postings that mention each requirement. The solid portion is where it was listed as a hard requirement rather than a preference."
          action={
            <Link to={`/jobs/${data.role.slug}/skills`} className="btn-secondary">
              All requirements
            </Link>
          }
        />

        {data.top_skills.length === 0 ? (
          <EmptyState
            title="No requirements extracted yet"
            body="There are not enough postings for this role to compute reliable statistics."
          />
        ) : (
          <div className="card p-5">
            <div className="divide-y divide-line">
              {data.top_skills.map((stat, i) => (
                <SkillBar key={stat.skill.slug} stat={stat} index={i} />
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
              <BarLegend />
              {data.top_skills[0] && <ConfidenceChip level={data.top_skills[0].confidence} />}
            </div>
          </div>
        )}
      </section>

      {/* Distributions -------------------------------------------------- */}
      <section className="mt-10 grid gap-5 lg:grid-cols-2">
        <div className="card p-5">
          <SectionHead title="Experience asked for" />
          <DistributionBars buckets={data.experience_distribution} />
        </div>
        <div className="card p-5">
          <SectionHead title="Education asked for" />
          <DistributionBars
            buckets={data.education_distribution}
            emptyLabel="No postings stated an education requirement."
          />
        </div>
      </section>

      {/* Emerging ------------------------------------------------------- */}
      <section className="mt-10">
        <SectionHead
          title="What's rising"
          hint="Skills whose share of postings is growing by more than sampling noise can explain."
          action={
            <Link to={`/trends?role=${data.role.slug}`} className="btn-secondary">
              Full trends
            </Link>
          }
        />

        {trends.loading && <LoadingBlock rows={3} label="Loading trends" />}

        {!trends.loading && emerging.length === 0 && (
          <div className="card p-5 text-sm text-muted">
            {trends.data?.note ?? 'No rising skills detected for this role yet.'}
          </div>
        )}

        {emerging.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2">
            {emerging.map((trend) => (
              <div key={trend.skill.slug} className="card flex items-center gap-4 p-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">{trend.skill.canonical}</p>
                    <DirectionChip direction={trend.direction} />
                  </div>
                  <p className="tnum mt-1 text-xs text-muted">
                    {trend.current_pct.toFixed(0)}% of postings today ·{' '}
                    <span className="font-medium text-low">
                      +{trend.change_pct.toFixed(1)}pp
                    </span>{' '}
                    over {trend.months_observed} months
                  </p>
                </div>
                <Sparkline trend={trend} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Sources -------------------------------------------------------- */}
      <section className="mt-10">
        <SectionHead title="Where this came from" />
        <div className="card divide-y divide-line">
          {data.sources.map((source) => (
            <div key={source.key} className="flex flex-wrap items-start gap-3 p-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{source.name}</p>
                {source.notes && <p className="mt-1 text-xs text-muted">{source.notes}</p>}
              </div>
              <span className="chip shrink-0">{source.kind.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </section>
    </Page>
  )
}
