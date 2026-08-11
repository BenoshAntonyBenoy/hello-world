// Mirrors backend/app/schemas.py. Kept hand-written rather than generated so
// the shapes stay readable; regenerate from /api/openapi.json if it grows.

export type Confidence = 'high' | 'medium' | 'low'
export type Priority = 'high' | 'medium' | 'low'
export type Proficiency = 'learning' | 'working' | 'strong'
export type TrendDirection = 'emerging' | 'declining' | 'stable' | 'insufficient_data'

export interface Skill {
  slug: string
  canonical: string
  category: string
  display_category: string
  tier: 'beginner' | 'intermediate' | 'advanced'
  description: string | null
}

export interface RoleSummary {
  slug: string
  title: string
  category: string
  summary: string | null
  analyzed_jobs: number
}

export interface Source {
  key: string
  name: string
  kind: string
  is_enabled: boolean
  notes: string | null
}

export interface SkillStat {
  skill: Skill
  frequency_pct: number
  required_pct: number
  preferred_pct: number
  jobs_mentioning: number
  total_jobs: number
  confidence: Confidence
  rank: number
  priority: Priority
}

export interface CategoryGroup {
  category: string
  label: string
  skills: SkillStat[]
}

export interface DistributionBucket {
  label: string
  count: number
  pct: number
}

export interface RoleAnalysis {
  role: RoleSummary
  analyzed_jobs: number
  total_ingested: number
  duplicates_removed: number
  filtered_irrelevant: number
  sources: Source[]
  last_updated: string | null
  window_start: string | null
  window_end: string | null
  top_skills: SkillStat[]
  groups: CategoryGroup[]
  experience_distribution: DistributionBucket[]
  education_distribution: DistributionBucket[]
  data_caveat: string
}

export interface TrendPoint {
  period: string
  frequency_pct: number
  total_jobs: number
  jobs_mentioning: number
}

export interface Trend {
  skill: Skill
  direction: TrendDirection
  change_pct: number
  current_pct: number
  slope_per_month: number
  months_observed: number
  points: TrendPoint[]
}

export interface RoleTrends {
  role: RoleSummary
  emerging: Trend[]
  declining: Trend[]
  stable: Trend[]
  note: string
}

export interface RoadmapItem {
  order: number
  skill: Skill
  frequency_pct: number
  confidence: Confidence
  priority: Priority
  reason: string
  prerequisites: string[]
  already_known: boolean
}

export interface RoadmapStage {
  tier: string
  label: string
  items: RoadmapItem[]
}

export interface Roadmap {
  role: RoleSummary
  analyzed_jobs: number
  stages: RoadmapStage[]
  note: string
}

export interface Job {
  id: number
  title: string
  company: string | null
  location: string | null
  employment_type: string | null
  experience: string | null
  min_years: number | null
  max_years: number | null
  education_level: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  key_skills: string[]
  source: string
  source_kind: string
  posted_at: string | null
  url: string | null
  is_sample_data: boolean
}

export interface JobList {
  role: RoleSummary
  total: number
  offset: number
  limit: number
  items: Job[]
  note: string
}

export interface ExtractedSkill {
  skill: Skill
  requirement_type: 'required' | 'preferred' | 'mentioned'
  mention_count: number
  confidence: number
  evidence: string
}

export interface AnalyzeResult {
  title: string
  matched_role: RoleSummary | null
  skills: ExtractedSkill[]
  groups: Record<string, ExtractedSkill[]>
  min_years: number | null
  max_years: number | null
  experience: string
  education_level: string | null
  education_fields: string[]
  salary_min: number | null
  salary_max: number | null
  comparison_note: string | null
}

export interface UserSkill {
  skill: Skill
  proficiency: Proficiency
}

export interface Profile {
  token: string
  target_role: RoleSummary | null
  skills: UserSkill[]
  privacy_note: string
}

export interface GapItem {
  skill: Skill
  frequency_pct: number
  confidence: Confidence
  priority: Priority
  proficiency: Proficiency | null
}

export interface SkillGap {
  role: RoleSummary
  readiness_pct: number
  analyzed_jobs: number
  explanation: string
  disclaimer: string
  high_priority: GapItem[]
  medium_priority: GapItem[]
  low_priority: GapItem[]
  already_strong: GapItem[]
}

export interface Health {
  status: string
  version: string
  database: string
  roles: number
  skills: number
  analyzed_jobs: number
  using_sample_data: boolean
}
