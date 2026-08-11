// Browser-side profile store for the static build.
//
// With no backend to talk to, the profile lives entirely in local storage.
// That is a smaller privacy surface than the hosted version, not a larger one:
// the skills never leave the device at all.

import type { Proficiency, RoleSummary, Skill } from './types'

const KEY = 'helloworld.local-profile'

export interface LocalProfile {
  skills: { skill: Skill; proficiency: Proficiency }[]
  targetRoleSlug: string | null
}

const EMPTY: LocalProfile = { skills: [], targetRoleSlug: null }

export function readLocalProfile(): LocalProfile {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return EMPTY
    const parsed = JSON.parse(raw) as LocalProfile
    if (!Array.isArray(parsed?.skills)) return EMPTY
    return { skills: parsed.skills, targetRoleSlug: parsed.targetRoleSlug ?? null }
  } catch {
    return EMPTY
  }
}

export function writeLocalProfile(profile: LocalProfile): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(profile))
  } catch {
    /* storage disabled — the profile simply will not persist */
  }
}

export function clearLocalProfile(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* nothing to do */
  }
}

export function knownSkillSlugs(): Set<string> {
  return new Set(readLocalProfile().skills.map((s) => s.skill.slug))
}

export function resolveTargetRole(
  roles: RoleSummary[],
  slug: string | null,
): RoleSummary | null {
  if (!slug) return null
  return roles.find((r) => r.slug === slug) ?? null
}
