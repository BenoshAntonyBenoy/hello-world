import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, isStaticBuild } from '@/lib/api'
import type { AnalyzeResult } from '@/lib/types'
import { usePageMeta } from '@/lib/hooks'
import { experienceLabel } from '@/lib/format'
import { Caveat, EmptyState, Page, SectionHead, StatTile, cx } from '@/components/ui'

const SAMPLE = `Senior Data Analyst — Bengaluru

About the role
You will partner with product and finance to turn messy data into decisions.

Responsibilities
Build and maintain reporting for the leadership team
Own our experimentation pipeline end to end

Requirements
Strong proficiency in SQL, including window functions
Advanced Excel — pivot tables, lookups, modelling
Hands-on experience with Power BI or Tableau
Working knowledge of Python (pandas)
3+ years of relevant experience
B.Tech degree in Computer Science, Statistics or a related discipline

Preferred Qualifications
Exposure to Amazon Web Services is a plus
Familiarity with dbt and Snowflake
Any experience with A/B testing will be an added advantage`

const TYPE_TONE: Record<string, string> = {
  required: 'border-brand/30 bg-brand-soft text-brand-ink',
  preferred: 'border-line bg-raised text-muted',
  mentioned: 'border-line bg-raised text-faint',
}

export default function Analyze() {
  usePageMeta(
    'Analyse a job description',
    'Paste a single job posting and see exactly which requirements it asks for, using the same extraction pipeline as the whole corpus.',
  )
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [result, setResult] = useState<AnalyzeResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.analyzeJob({
        description: text,
        title: title.trim() || undefined,
      })
      setResult(data)
    } catch (err) {
      setResult(null)
      setError(
        err instanceof ApiError && err.status === 422
          ? 'That description is too short to analyse. Paste at least a few sentences.'
          : err instanceof Error
            ? err.message
            : 'Could not analyse that description.',
      )
    } finally {
      setLoading(false)
    }
  }

  const required = result?.skills.filter((s) => s.requirement_type === 'required') ?? []
  const preferred = result?.skills.filter((s) => s.requirement_type === 'preferred') ?? []

  const header = (
    <div>
      <p className="label">Analyse a single posting</p>
      <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
        Paste a job description
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Runs the same extraction pipeline used across the whole corpus. Useful for a role we
        do not cover, or to see exactly what one posting is asking for.
      </p>
    </div>
  )

  // Extraction is a Python service. A static deployment has nowhere to run it,
  // so say that plainly instead of offering a button that always fails.
  if (isStaticBuild) {
    return (
      <Page>
        {header}
        <div className="mt-8">
          <EmptyState
            title="Not available in this demo"
            body={
              'This page runs the taxonomy matcher and section parser, which live in ' +
              'the Python backend. The published demo is a static build with no server ' +
              'behind it, so there is nothing here to run them. Everything else on the ' +
              'site works — those pages read analysis that was computed ahead of time.'
            }
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <Link to="/search" className="btn-primary">
                  Browse the analysed roles
                </Link>
                <a
                  href="https://github.com/gokul-k101/hello-world#quick-start"
                  target="_blank"
                  rel="noreferrer noopener"
                  className="btn-secondary"
                >
                  Run it locally ↗
                </a>
              </div>
            }
          />
        </div>
      </Page>
    )
  }

  return (
    <Page>
      {header}

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
        <section>
          <SectionHead title="Input" />
          <div className="space-y-3">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Job title (optional — helps us match a role)"
              aria-label="Job title"
              className="input"
            />
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={18}
              placeholder="Paste the full job description here…"
              aria-label="Job description"
              className="input resize-y font-mono text-xs leading-relaxed"
            />
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={run}
                disabled={loading || text.trim().length < 40}
                className="btn-primary"
              >
                {loading ? 'Analysing…' : 'Extract requirements'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setText(SAMPLE)
                  setTitle('Senior Data Analyst')
                }}
                className="btn-secondary"
              >
                Use a sample
              </button>
              {text.trim().length > 0 && text.trim().length < 40 && (
                <span className="text-xs text-muted">
                  {40 - text.trim().length} more characters needed
                </span>
              )}
            </div>
            {error && (
              <p className="text-sm text-high" role="alert">
                {error}
              </p>
            )}
          </div>
        </section>

        <section>
          <SectionHead title="Extracted" />

          {!result && !loading && (
            <div className="card p-10 text-center text-sm text-muted">
              Results will appear here. Nothing you paste is added to the public statistics.
            </div>
          )}

          {loading && <div className="card h-64 animate-pulse bg-raised" />}

          {result && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-3">
                <StatTile
                  label="Experience"
                  value={
                    <span className="text-lg">
                      {experienceLabel(result.min_years, result.max_years)}
                    </span>
                  }
                />
                <StatTile
                  label="Education"
                  value={
                    <span className="text-lg">{result.education_level ?? 'Not stated'}</span>
                  }
                  hint={result.education_fields.join(', ') || undefined}
                />
              </div>

              {result.matched_role && (
                <div className="card flex flex-wrap items-center justify-between gap-3 p-4">
                  <div>
                    <p className="label">Closest role we analyse</p>
                    <p className="mt-1 text-sm font-medium">{result.matched_role.title}</p>
                  </div>
                  <Link to={`/jobs/${result.matched_role.slug}`} className="btn-secondary">
                    Compare with the market →
                  </Link>
                </div>
              )}

              {result.comparison_note && <Caveat>{result.comparison_note}</Caveat>}

              {[
                { label: 'Required', items: required },
                { label: 'Preferred', items: preferred },
              ].map(
                (block) =>
                  block.items.length > 0 && (
                    <div key={block.label}>
                      <p className="label mb-2">
                        {block.label} ({block.items.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {block.items.map((item) => (
                          <span
                            key={item.skill.slug}
                            title={item.evidence}
                            className={cx('chip', TYPE_TONE[item.requirement_type])}
                          >
                            {item.skill.canonical}
                          </span>
                        ))}
                      </div>
                    </div>
                  ),
              )}

              {result.skills.length === 0 && (
                <div className="card p-6 text-center text-sm text-muted">
                  No known requirements were found. The posting may be very short, or written
                  in terms our vocabulary does not cover yet.
                </div>
              )}

              <p className="text-xs text-faint">
                Hover a skill to see the sentence it was extracted from.
              </p>
            </div>
          )}
        </section>
      </div>
    </Page>
  )
}
