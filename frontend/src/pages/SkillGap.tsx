import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { count } from '@/lib/format'
import { ReadinessRing } from '@/components/charts'
import type { GapItem } from '@/lib/types'
import {
  Caveat,
  EmptyState,
  ErrorState,
  Page,
  SectionHead,
  Skeleton,
  cx,
} from '@/components/ui'

function GapList({
  items,
  tone,
  title,
  hint,
}: {
  items: GapItem[]
  tone: 'high' | 'medium' | 'low' | 'strong'
  title: string
  hint: string
}) {
  const dot = {
    high: 'bg-high',
    medium: 'bg-medium',
    low: 'bg-faint',
    strong: 'bg-low',
  }[tone]

  return (
    <section>
      <SectionHead title={title} hint={hint} />
      {items.length === 0 ? (
        <div className="card p-5 text-sm text-muted">Nothing in this group.</div>
      ) : (
        <ul className="card divide-y divide-line">
          {items.map((item) => (
            <li key={item.skill.slug} className="flex items-center gap-3 p-3.5">
              <span className={cx('h-2 w-2 shrink-0 rounded-full', dot)} aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.skill.canonical}</p>
                <p className="truncate text-xs text-muted">
                  {item.skill.display_category}
                  {item.proficiency && ` · you marked this “${item.proficiency}”`}
                </p>
              </div>
              <span className="tnum shrink-0 text-sm font-semibold">
                {item.frequency_pct.toFixed(0)}%
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default function SkillGap() {
  const [params, setParams] = useSearchParams()
  const roles = useAsync(() => api.roles(), [])
  const profile = useAsync(() => api.profile(), [])

  const [role, setRole] = useState(params.get('role') ?? '')

  // Default to the target role saved on the profile, if there is one.
  useEffect(() => {
    if (role || !profile.data?.target_role) return
    setRole(profile.data.target_role.slug)
  }, [profile.data, role])

  const effectiveRole = role || params.get('role') || ''
  const gap = useAsync(
    () => api.skillGap(effectiveRole),
    [effectiveRole],
    Boolean(effectiveRole),
  )

  const hasSkills = (profile.data?.skills.length ?? 0) > 0

  return (
    <Page>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label">Skill gap analysis</p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
            How ready are you, and for what?
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            We compare the skills on your profile against what postings for a role actually
            ask for, weighted by how often each one appears.
          </p>
        </div>

        <label className="shrink-0">
          <span className="label mb-1.5 block">Compare against</span>
          <select
            className="input min-w-[15rem] cursor-pointer"
            value={effectiveRole}
            onChange={(e) => {
              setRole(e.target.value)
              setParams(e.target.value ? { role: e.target.value } : {})
            }}
          >
            <option value="">Choose a role…</option>
            {(roles.data ?? []).map((r) => (
              <option key={r.slug} value={r.slug}>
                {r.title}
              </option>
            ))}
          </select>
        </label>
      </div>

      {!profile.loading && !hasSkills && (
        <div className="mt-8">
          <EmptyState
            title="Your profile is empty"
            body="Add a few skills you already have and we can work out how much of a role's demand you already cover."
            action={
              <Link to="/profile" className="btn-primary">
                Build my profile
              </Link>
            }
          />
        </div>
      )}

      {hasSkills && !effectiveRole && (
        <div className="mt-8">
          <EmptyState
            title="Pick a role to compare against"
            body="Choose a target role above and we will show your readiness and the gaps worth closing first."
          />
        </div>
      )}

      {effectiveRole && gap.loading && <Skeleton className="mt-8 h-72" />}

      {effectiveRole && gap.error && !gap.notFound && (
        <div className="mt-8">
          <ErrorState message={gap.error} onRetry={gap.reload} />
        </div>
      )}

      {gap.data && !gap.loading && (
        <>
          <div className="card mt-8 flex flex-col items-center gap-6 p-6 sm:flex-row sm:p-8">
            <ReadinessRing value={gap.data.readiness_pct} />
            <div className="min-w-0 flex-1 text-center sm:text-left">
              <h2 className="text-xl font-semibold tracking-tight">
                {gap.data.role.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{gap.data.explanation}</p>
              <p className="tnum mt-3 text-xs text-faint">
                Based on {count(gap.data.analyzed_jobs)} analysed postings
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start">
                <Link to={`/jobs/${gap.data.role.slug}/roadmap`} className="btn-primary">
                  Get my learning plan
                </Link>
                <Link to="/profile" className="btn-secondary">
                  Edit my skills
                </Link>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <Caveat>{gap.data.disclaimer}</Caveat>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <GapList
              items={gap.data.high_priority}
              tone="high"
              title="High priority"
              hint="Missing, and requested in at least half of postings."
            />
            <GapList
              items={gap.data.already_strong}
              tone="strong"
              title="Already strong"
              hint="On your profile and genuinely in demand."
            />
            <GapList
              items={gap.data.medium_priority}
              tone="medium"
              title="Medium priority"
              hint="Missing, requested in a quarter to a half of postings."
            />
            <GapList
              items={gap.data.low_priority}
              tone="low"
              title="Lower priority"
              hint="Missing, but requested less often. Worth knowing eventually."
            />
          </div>
        </>
      )}
    </Page>
  )
}
