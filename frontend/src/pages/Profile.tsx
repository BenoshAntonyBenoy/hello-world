import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { clearProfileToken } from '@/lib/profile'
import { useAsync, useDebounced } from '@/lib/hooks'
import type { Proficiency, Skill } from '@/lib/types'
import {
  Caveat,
  EmptyState,
  ErrorState,
  Page,
  SectionHead,
  Skeleton,
  cx,
} from '@/components/ui'

interface SelectedSkill {
  skill: Skill
  proficiency: Proficiency
}

const LEVELS: { key: Proficiency; label: string; hint: string }[] = [
  { key: 'learning', label: 'Learning', hint: 'Started, not yet comfortable' },
  { key: 'working', label: 'Working', hint: 'Can use it on real tasks' },
  { key: 'strong', label: 'Strong', hint: 'Confident, could teach it' },
]

export default function Profile() {
  const profile = useAsync(() => api.profile(), [])
  const roles = useAsync(() => api.roles(), [])

  // Holds the full Skill object, not just the slug. Resolving names from the
  // live search results instead would make already-added skills vanish from
  // the list the moment the user searches for something else.
  const [selected, setSelected] = useState<Map<string, SelectedSkill>>(new Map())
  const [target, setTarget] = useState<string>('')
  const [query, setQuery] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [dirty, setDirty] = useState(false)

  const debouncedQuery = useDebounced(query, 200)
  const search = useAsync(
    () => api.skills(debouncedQuery.trim() || undefined),
    [debouncedQuery],
  )

  // Seed local state once the server profile arrives.
  useEffect(() => {
    if (!profile.data) return
    setSelected(
      new Map(
        profile.data.skills.map((s) => [
          s.skill.slug,
          { skill: s.skill, proficiency: s.proficiency },
        ]),
      ),
    )
    setTarget(profile.data.target_role?.slug ?? '')
  }, [profile.data])

  const selectedSkills = useMemo(
    () =>
      [...selected.values()].sort((a, b) =>
        a.skill.canonical.localeCompare(b.skill.canonical),
      ),
    [selected],
  )

  const results = (search.data ?? []).filter((s) => !selected.has(s.slug)).slice(0, 40)

  function toggle(skill: Skill) {
    setSelected((prev) => {
      const next = new Map(prev)
      if (next.has(skill.slug)) next.delete(skill.slug)
      else next.set(skill.slug, { skill, proficiency: 'working' })
      return next
    })
    setDirty(true)
    setSaved(false)
  }

  function setLevel(slug: string, level: Proficiency) {
    setSelected((prev) => {
      const current = prev.get(slug)
      if (!current) return prev
      return new Map(prev).set(slug, { ...current, proficiency: level })
    })
    setDirty(true)
    setSaved(false)
  }

  async function save() {
    setSaving(true)
    setSaveError(null)
    try {
      await api.saveSkills(
        [...selected.entries()].map(([skill_slug, entry]) => ({
          skill_slug,
          proficiency: entry.proficiency,
        })),
        target || null,
      )
      setSaved(true)
      setDirty(false)
      profile.reload()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Could not save your profile.')
    } finally {
      setSaving(false)
    }
  }

  async function wipe() {
    if (!confirm('Delete your profile and every skill in it? This cannot be undone.')) return
    try {
      await api.deleteProfile()
      clearProfileToken()
      setSelected(new Map())
      setTarget('')
      setDirty(false)
      setSaved(false)
      profile.reload()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Could not delete your profile.')
    }
  }

  return (
    <Page>
      <div>
        <p className="label">Your skill profile</p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">What can you do today?</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Pick the skills you already have. We compare them against real demand to show what is
          worth learning next — nothing here is shared, and there is no account to create.
        </p>
      </div>

      {profile.error && (
        <div className="mt-6">
          <ErrorState message={profile.error} onRetry={profile.reload} />
        </div>
      )}

      {profile.loading && <Skeleton className="mt-6 h-96" />}

      {profile.data && (
        <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          {/* Picker ------------------------------------------------- */}
          <section>
            <SectionHead
              title="Add your skills"
              hint="Search the requirement vocabulary and click to add."
            />

            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search skills, tools, certifications…"
              aria-label="Search skills"
              className="input"
            />

            <div className="mt-3 max-h-[26rem] overflow-y-auto rounded-xl border border-line bg-surface p-1.5">
              {search.loading && (
                <div className="space-y-1.5 p-1.5">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-9" />
                  ))}
                </div>
              )}

              {!search.loading && results.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-muted">
                  {query.trim()
                    ? `Nothing matches “${query.trim()}”.`
                    : 'Everything matching is already in your profile.'}
                </p>
              )}

              {results.map((skill) => (
                <button
                  key={skill.slug}
                  type="button"
                  onClick={() => toggle(skill)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-raised"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm">{skill.canonical}</span>
                    <span className="block truncate text-xs text-faint">
                      {skill.display_category} · {skill.tier}
                    </span>
                  </span>
                  <span className="shrink-0 text-lg leading-none text-faint">+</span>
                </button>
              ))}
            </div>
          </section>

          {/* Selected ----------------------------------------------- */}
          <section>
            <SectionHead
              title={`Your skills (${selected.size})`}
              hint="Set how confident you are with each — it weights your readiness score."
            />

            {selectedSkills.length === 0 ? (
              <EmptyState
                title="No skills added yet"
                body="Search on the left and click a skill to add it. Three or four is enough to get a useful readiness score."
              />
            ) : (
              <ul className="card max-h-[26rem] divide-y divide-line overflow-y-auto">
                {selectedSkills.map(({ skill, proficiency }) => (
                  <li key={skill.slug} className="p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="min-w-0 truncate text-sm font-medium">
                        {skill.canonical}
                      </span>
                      <button
                        type="button"
                        onClick={() => toggle(skill)}
                        aria-label={`Remove ${skill.canonical}`}
                        className="shrink-0 rounded-md p-1 text-faint transition-colors hover:bg-raised hover:text-high"
                      >
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                          <path d="M18 6 6 18M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <div className="mt-2 flex gap-1">
                      {LEVELS.map((level) => (
                        <button
                          key={level.key}
                          type="button"
                          title={level.hint}
                          onClick={() => setLevel(skill.slug, level.key)}
                          aria-pressed={proficiency === level.key}
                          className={cx(
                            'flex-1 rounded-md border px-2 py-1 text-2xs font-medium transition-colors',
                            proficiency === level.key
                              ? 'border-brand bg-brand-soft text-brand-ink'
                              : 'border-line text-muted hover:bg-raised',
                          )}
                        >
                          {level.label}
                        </button>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-5">
              <label className="label mb-1.5 block" htmlFor="target-role">
                Target role (optional)
              </label>
              <select
                id="target-role"
                className="input cursor-pointer"
                value={target}
                onChange={(e) => {
                  setTarget(e.target.value)
                  setDirty(true)
                  setSaved(false)
                }}
              >
                <option value="">No target selected</option>
                {(roles.data ?? []).map((role) => (
                  <option key={role.slug} value={role.slug}>
                    {role.title}
                  </option>
                ))}
              </select>
            </div>

            {saveError && (
              <p className="mt-3 text-sm text-high" role="alert">
                {saveError}
              </p>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={save}
                disabled={saving || !dirty}
                className="btn-primary"
              >
                {saving ? 'Saving…' : dirty ? 'Save profile' : 'Saved'}
              </button>
              {saved && (
                <Link to="/skill-gap" className="btn-secondary">
                  See my skill gap →
                </Link>
              )}
              <button type="button" onClick={wipe} className="btn-ghost ml-auto text-high">
                Delete my data
              </button>
            </div>
          </section>
        </div>
      )}

      {profile.data && (
        <div className="mt-8">
          <Caveat>{profile.data.privacy_note}</Caveat>
        </div>
      )}
    </Page>
  )
}
