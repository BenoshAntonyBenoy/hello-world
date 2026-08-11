import type {
  AnalyzeResult,
  CategoryGroup,
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
  Source,
} from './types'
import { ApiError, UnsupportedInStaticBuild } from './apiError'
import { getProfileToken } from './profile'
import { staticApi } from './staticApi'

export { ApiError, UnsupportedInStaticBuild }

/**
 * Whether this bundle was built to run without a backend.
 *
 * Set by `VITE_STATIC_DATA=true` at build time (see the Pages workflow). Pages
 * check it to explain, rather than silently hide, the features that need the
 * Python service.
 */
export const isStaticBuild = import.meta.env.VITE_STATIC_DATA === 'true'

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    })
  } catch {
    // A network-level failure is almost always "the API isn't running", which
    // deserves a clearer message than the browser's generic TypeError.
    throw new ApiError(
      'Could not reach the API. Is the backend running on port 8010?',
      0,
    )
  }

  if (res.status === 204) return undefined as T

  const text = await res.text()
  let body: unknown = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = null
  }

  if (!res.ok) {
    const detail =
      body && typeof body === 'object' && 'detail' in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed with status ${res.status}`
    throw new ApiError(detail, res.status)
  }

  return body as T
}

function withToken(init: RequestInit = {}): RequestInit {
  return {
    ...init,
    headers: { ...(init.headers ?? {}), 'X-Profile-Token': getProfileToken() },
  }
}

const liveApi = {
  health: () => request<Health>('/api/health'),
  sources: () => request<Source[]>('/api/sources'),

  roles: () => request<RoleSummary[]>('/api/roles'),
  searchRoles: (q: string) =>
    request<RoleSummary[]>(`/api/search?q=${encodeURIComponent(q)}`),

  role: (slug: string) => request<RoleAnalysis>(`/api/roles/${encodeURIComponent(slug)}`),
  roleSkills: (slug: string) =>
    request<CategoryGroup[]>(`/api/roles/${encodeURIComponent(slug)}/skills`),
  roleTrends: (slug: string) =>
    request<RoleTrends>(`/api/roles/${encodeURIComponent(slug)}/trends`),
  roleRoadmap: (slug: string, useProfile = false) =>
    request<Roadmap>(
      `/api/roles/${encodeURIComponent(slug)}/roadmap` +
        (useProfile ? `?profile_token=${encodeURIComponent(getProfileToken())}` : ''),
    ),
  roleJobs: (slug: string, limit = 20, offset = 0) =>
    request<JobList>(
      `/api/roles/${encodeURIComponent(slug)}/jobs?limit=${limit}&offset=${offset}`,
    ),

  skills: (q?: string) =>
    request<Skill[]>(`/api/skills${q ? `?q=${encodeURIComponent(q)}` : ''}`),

  analyzeJob: (payload: { description: string; title?: string; company?: string }) =>
    request<AnalyzeResult>('/api/analyze-job', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  profile: () => request<Profile>('/api/profile', withToken()),
  saveSkills: (
    skills: { skill_slug: string; proficiency: Proficiency }[],
    targetRoleSlug?: string | null,
  ) =>
    request<Profile>(
      '/api/profile/skills',
      withToken({
        method: 'POST',
        body: JSON.stringify({
          skills,
          target_role_slug: targetRoleSlug ?? null,
        }),
      }),
    ),
  deleteProfile: () => request<void>('/api/profile', withToken({ method: 'DELETE' })),
  skillGap: (slug: string) =>
    request<SkillGap>(`/api/profile/skill-gap/${encodeURIComponent(slug)}`, withToken()),
}

/**
 * The two clients are interchangeable by design: pages call `api.role(slug)`
 * without knowing whether that hits FastAPI or a frozen JSON document.
 */
export const api = isStaticBuild ? (staticApi as typeof liveApi) : liveApi
