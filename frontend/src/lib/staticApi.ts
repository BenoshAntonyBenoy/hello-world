// Static-build API client.
//
// Same surface as the live client, but every read is a fetch of a JSON file
// frozen at build time by `backend/export_static.py`. Anything the backend
// would have computed per-request — search, pagination, the skill gap — is
// computed here instead, from those same documents.
//
// Two capabilities genuinely cannot survive the trip:
//   * POST /api/analyze-job needs the Python extractor → the page is disabled
//   * profile writes have nowhere to go → they land in local storage

import { ApiError, UnsupportedInStaticBuild } from './apiError'
import {
  clearLocalProfile,
  knownSkillSlugs,
  readLocalProfile,
  resolveTargetRole,
  writeLocalProfile,
} from './localProfile'
import type {
  CategoryGroup,
  GapItem,
  Health,
  JobList,
  Profile,
  Proficiency,
  Roadmap,
  RoleAnalysis,
  RoleSummary,
  RoleTrends,
  Skill,
  SkillGap,
  SkillStat,
  Source,
} from './types'

const BASE = import.meta.env.BASE_URL || '/'

async function doc<T>(path: string): Promise<T> {
  let res: Response
  try {
    // "data", not "api" — /api/* is reserved for the serverless analyser.
    // Written by backend/export_static.py; the two must stay in step.
    res = await fetch(`${BASE}data/${path}`)
  } catch {
    throw new ApiError('Could not load the demo data files.', 0)
  }

  if (res.status === 404) {
    throw new ApiError('No analysed data for this page.', 404)
  }
  if (!res.ok) {
    throw new ApiError(`Failed to load demo data (${res.status}).`, res.status)
  }

  // The SPA fallback means a missing file can come back as index.html with a
  // 200 rather than a 404 — GitHub Pages sets the status correctly, but local
  // `vite preview` and several static hosts do not. Without this check, asking
  // for a role that was never analysed yields a JSON parse error instead of the
  // "we haven't analysed that yet" page.
  const body = await res.text()
  if (!body.trimStart().startsWith('{') && !body.trimStart().startsWith('[')) {
    throw new ApiError('No analysed data for this page.', 404)
  }

  try {
    return JSON.parse(body) as T
  } catch {
    throw new ApiError('No analysed data for this page.', 404)
  }
}

// --- Skill-gap scoring -------------------------------------------------------
//
// Mirrors backend/app/analytics/skillgap.py. The two must stay in step; if you
// change the weighting there, change it here. Kept as a deliberate duplicate
// rather than an extra build step, because it is a dozen lines of arithmetic
// and the alternative is shipping a Python runtime to the browser.

const FREQUENCY_FLOOR = 8.0
const PROFICIENCY_WEIGHT: Record<Proficiency, number> = {
  strong: 1.0,
  working: 0.85,
  learning: 0.45,
}

const DISCLAIMER =
  'Readiness measures how much of this role’s commonly requested skill set you ' +
  'currently cover, based on analysed postings. It is not a prediction of hiring ' +
  'outcomes and does not account for interviews, portfolio, referrals or current ' +
  'openings.'

function priorityFor(frequency: number): 'high' | 'medium' | 'low' {
  if (frequency >= 50) return 'high'
  if (frequency >= 25) return 'medium'
  return 'low'
}

function flatten(groups: CategoryGroup[]): SkillStat[] {
  return groups
    .flatMap((g) => g.skills)
    .filter((s) => s.frequency_pct >= FREQUENCY_FLOOR)
    .sort((a, b) => b.frequency_pct - a.frequency_pct)
}

function explain(role: RoleSummary, covered: number, missing: number, jobs: number, high: GapItem[]): string {
  const parts = [
    `You cover ${covered} of the ${covered + missing} skills commonly requested ` +
      `for ${role.title}, weighted by how often each one appears across ` +
      `${jobs.toLocaleString('en-IN')} analysed postings.`,
  ]
  if (high.length) {
    parts.push(
      `The largest gaps are ${high.slice(0, 3).map((i) => i.skill.canonical).join(', ')} — ` +
        'each appears in at least half of these postings.',
    )
  } else if (missing) {
    parts.push(
      'No high-frequency skills are missing; the remaining gaps are in moderately requested areas.',
    )
  } else {
    parts.push('You cover every frequently requested skill for this role.')
  }
  return parts.join(' ')
}

// --- Client ------------------------------------------------------------------

export const staticApi = {
  health: () => doc<Health>('health.json'),
  sources: () => doc<Source[]>('sources.json'),
  roles: () => doc<RoleSummary[]>('roles.json'),

  async searchRoles(q: string): Promise<RoleSummary[]> {
    const needle = q.trim().toLowerCase()
    const roles = await doc<RoleSummary[]>('roles.json')
    if (!needle) return roles.slice(0, 8)
    return roles
      .filter(
        (r) =>
          r.title.toLowerCase().includes(needle) ||
          r.category.toLowerCase().includes(needle) ||
          r.slug.includes(needle),
      )
      .sort((a, b) => {
        const aStarts = a.title.toLowerCase().startsWith(needle) ? 0 : 1
        const bStarts = b.title.toLowerCase().startsWith(needle) ? 0 : 1
        return aStarts - bStarts || a.title.length - b.title.length
      })
      .slice(0, 8)
  },

  role: (slug: string) => doc<RoleAnalysis>(`roles/${slug}.json`),
  roleSkills: (slug: string) => doc<CategoryGroup[]>(`roles/${slug}/skills.json`),
  roleTrends: (slug: string) => doc<RoleTrends>(`roles/${slug}/trends.json`),

  async roleRoadmap(slug: string, useProfile = false): Promise<Roadmap> {
    const roadmap = await doc<Roadmap>(`roles/${slug}/roadmap.json`)
    if (!useProfile) return roadmap
    // The exported roadmap knows nothing about this browser's profile, so the
    // "you already have this" marks are applied here.
    const known = knownSkillSlugs()
    return {
      ...roadmap,
      stages: roadmap.stages.map((stage) => ({
        ...stage,
        items: stage.items.map((item) => ({
          ...item,
          already_known: known.has(item.skill.slug),
        })),
      })),
    }
  },

  async roleJobs(slug: string, limit = 20, offset = 0): Promise<JobList> {
    const all = await doc<JobList>(`roles/${slug}/jobs.json`)
    const exported = all.items.length
    return {
      ...all,
      // `total` becomes the exported count so pagination stops at the last
      // page that actually has postings. The real corpus size is stated in the
      // note instead of being implied by a page count that leads nowhere.
      total: exported,
      offset,
      limit,
      items: all.items.slice(offset, offset + limit),
      note:
        `${all.note} Showing the ${exported} most recent of the ` +
        `${all.total.toLocaleString('en-IN')} postings analysed for this role.`,
    }
  },

  async skills(q?: string): Promise<Skill[]> {
    const all = await doc<Skill[]>('skills.json')
    if (!q?.trim()) return all
    const needle = q.trim().toLowerCase()
    return all.filter((s) => s.canonical.toLowerCase().includes(needle))
  },

  analyzeJob(): Promise<never> {
    return Promise.reject(new UnsupportedInStaticBuild('The job description analyser'))
  },

  async profile(): Promise<Profile> {
    const local = readLocalProfile()
    const roles = await doc<RoleSummary[]>('roles.json')
    return {
      token: 'local',
      target_role: resolveTargetRole(roles, local.targetRoleSlug),
      skills: local.skills,
      privacy_note:
        'This is the static demo, so your profile never leaves this browser — ' +
        'it is stored in local storage and is not sent anywhere at all. ' +
        'Deleting it removes every trace.',
    }
  },

  async saveSkills(
    skills: { skill_slug: string; proficiency: Proficiency }[],
    targetRoleSlug?: string | null,
  ): Promise<Profile> {
    const catalog = await doc<Skill[]>('skills.json')
    const bySlug = new Map(catalog.map((s) => [s.slug, s]))

    const unknown = skills.filter((s) => !bySlug.has(s.skill_slug))
    if (unknown.length) {
      throw new ApiError(
        `Unknown skill slugs: ${unknown.map((s) => s.skill_slug).join(', ')}`,
        400,
      )
    }

    writeLocalProfile({
      skills: skills.map((s) => ({
        skill: bySlug.get(s.skill_slug)!,
        proficiency: s.proficiency,
      })),
      targetRoleSlug: targetRoleSlug ?? null,
    })
    return this.profile()
  },

  async deleteProfile(): Promise<void> {
    clearLocalProfile()
  },

  async skillGap(slug: string): Promise<SkillGap> {
    const [groups, roleData] = await Promise.all([
      doc<CategoryGroup[]>(`roles/${slug}/skills.json`),
      doc<RoleAnalysis>(`roles/${slug}.json`),
    ])
    const role = roleData.role
    const stats = flatten(groups)
    const local = readLocalProfile()
    const proficiencyBySlug = new Map(
      local.skills.map((s) => [s.skill.slug, s.proficiency]),
    )

    const result: SkillGap = {
      role,
      readiness_pct: 0,
      analyzed_jobs: stats[0]?.total_jobs ?? roleData.analyzed_jobs,
      explanation: '',
      disclaimer: DISCLAIMER,
      high_priority: [],
      medium_priority: [],
      low_priority: [],
      already_strong: [],
    }

    if (!stats.length) {
      result.explanation = `No analysed postings for ${role.title} yet, so there is nothing to compare against.`
      return result
    }

    let totalWeight = 0
    let coveredWeight = 0

    for (const stat of stats) {
      totalWeight += stat.frequency_pct
      const proficiency = proficiencyBySlug.get(stat.skill.slug) ?? null
      const item: GapItem = {
        skill: stat.skill,
        frequency_pct: stat.frequency_pct,
        confidence: stat.confidence,
        priority: priorityFor(stat.frequency_pct),
        proficiency,
      }

      if (proficiency) {
        coveredWeight += stat.frequency_pct * (PROFICIENCY_WEIGHT[proficiency] ?? 0.85)
        result.already_strong.push(item)
      } else if (item.priority === 'high') {
        result.high_priority.push(item)
      } else if (item.priority === 'medium') {
        result.medium_priority.push(item)
      } else {
        result.low_priority.push(item)
      }
    }

    result.readiness_pct = totalWeight
      ? Math.round((coveredWeight / totalWeight) * 1000) / 10
      : 0

    const missing =
      result.high_priority.length +
      result.medium_priority.length +
      result.low_priority.length
    result.explanation = explain(
      role,
      result.already_strong.length,
      missing,
      result.analyzed_jobs,
      result.high_priority,
    )
    return result
  },
}
