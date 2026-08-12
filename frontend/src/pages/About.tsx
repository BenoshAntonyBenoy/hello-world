import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { DOCS_LINK } from '@/components/Layout'
import { useAsync, usePageMeta } from '@/lib/hooks'
import { count } from '@/lib/format'
import { Caveat, Page, SectionHead, StatTile } from '@/components/ui'

export default function About() {
  usePageMeta(
    'About & data sources',
    'How a number gets made: where the postings come from, how requirements are extracted and counted, and what the figures do not mean.',
  )
  const health = useAsync(() => api.health(), [])
  const sources = useAsync(() => api.sources(), [])

  return (
    <Page className="max-w-3xl">
      <p className="label">About</p>
      <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
        Observe what companies ask for. Explain it. Help people prioritise.
      </h1>
      <p className="mt-4 text-sm leading-relaxed text-muted">
        hello-world does not tell you what to study based on a curriculum. It reads job
        postings, counts what recurs, and reports the result with the sample size attached.
        The goal is not to replace universities — it is to make the gap between what is taught
        and what is hired for visible to the person it affects.
      </p>

      {health.data && (
        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          <StatTile label="Postings analysed" value={count(health.data.analyzed_jobs)} />
          <StatTile label="Roles covered" value={health.data.roles} />
          <StatTile label="Requirements tracked" value={health.data.skills} />
        </div>
      )}

      <section className="mt-10">
        <SectionHead title="How a number gets made" />
        <ol className="card divide-y divide-line text-sm">
          {[
            [
              'Collect',
              'Postings arrive through a connector layer. Each connector declares how it legally obtains data — official API, licensed dataset, public feed, or user-submitted.',
            ],
            [
              'Deduplicate',
              'Exact reposts are dropped and near-identical relists are flagged. Counting one company’s listing eight times would turn their stack into an industry trend.',
            ],
            [
              'Filter',
              'Postings that do not actually match the role are scored down and excluded, so a mis-titled sales listing cannot pollute a Data Analyst breakdown.',
            ],
            [
              'Extract',
              'Each posting is split into sections so a hard requirement can be told apart from a nice-to-have. Synonyms collapse: ReactJS, React.js and React are one skill. Degree lines are excluded from skill counts, so "B.Tech in Statistics" does not inflate Statistics as a working skill.',
            ],
            [
              'Count',
              'Frequency is postings mentioning the skill divided by relevant postings analysed. Every figure carries a confidence rating driven by sample size, not by how large the percentage looks.',
            ],
            [
              'Sequence',
              'Demand becomes a learning path ordered by prerequisite depth, so nothing is recommended before its foundation.',
            ],
          ].map(([title, body]) => (
            <li key={title} className="p-4">
              <p className="font-medium">{title}</p>
              <p className="mt-1 leading-relaxed text-muted">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-10">
        <SectionHead
          title="Where the data comes from"
          hint="Every source declares its legal basis. We do not scrape job boards."
        />
        <div className="card divide-y divide-line">
          {(sources.data ?? []).map((source) => (
            <div key={source.key} className="p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-medium">{source.name}</p>
                <span className="chip">{source.kind.replace('_', ' ')}</span>
              </div>
              {source.notes && (
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{source.notes}</p>
              )}
            </div>
          ))}
        </div>

        {health.data?.using_sample_data && (
          <div className="mt-4">
            <Caveat>
              This deployment is running on a synthetic sample corpus. Companies in it are
              fictional and the figures demonstrate the pipeline rather than describing the
              real job market. Connect a licensed feed or official API before treating any
              number here as market fact.
            </Caveat>
          </div>
        )}
      </section>

      <section className="mt-10">
        <SectionHead title="What the numbers do not mean" />
        <div className="card space-y-3 p-5 text-sm leading-relaxed text-muted">
          <p>
            <span className="font-medium text-ink">A readiness score is not a hiring
            probability.</span>{' '}
            It measures how much of a role's commonly requested skill set you cover. It knows
            nothing about your interviews, your portfolio, your network, or whether anyone is
            hiring this quarter.
          </p>
          <p>
            <span className="font-medium text-ink">Frequency is not importance.</span> A skill
            in 90% of postings is common, which usually means necessary but rarely means
            sufficient. The rare skill in 8% of postings may be exactly what differentiates you.
          </p>
          <p>
            <span className="font-medium text-ink">Coverage is partial.</span> No corpus sees
            every posting. Roles, regions and seniority levels are unevenly represented, and
            small samples are labelled as such rather than quietly rounded up.
          </p>
        </div>
      </section>

      <section className="mt-10">
        <SectionHead title="Your data" />
        <div className="card p-5 text-sm leading-relaxed text-muted">
          <p>
            Profiles are identified by a token your browser generates. There is no account, no
            email address, no password and no third-party tracking. The only thing stored is
            the list of skills you selected — and{' '}
            <Link to="/profile" className="link">
              deleting your profile
            </Link>{' '}
            removes every row we hold.
          </p>
          <p className="mt-3">
            Job descriptions you paste into the analyser are held in memory for the life of the
            process and are never merged into published statistics.
          </p>
        </div>
      </section>

      <div className="mt-10 flex flex-wrap gap-2">
        <Link to="/search" className="btn-primary">
          Start with a role
        </Link>
        <a
          href={DOCS_LINK.href}
          target="_blank"
          rel="noreferrer noopener"
          className="btn-secondary"
        >
          {DOCS_LINK.label === 'API docs' ? 'Read the API docs' : DOCS_LINK.label}
        </a>
      </div>
    </Page>
  )
}
