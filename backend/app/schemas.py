"""Pydantic response and request models.

These are the API contract. They are deliberately separate from the ORM models
so the database can change shape without breaking clients, and so nothing
internal (raw description text, relevance scores, duplicate bookkeeping) leaks
into a public response by accident.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Reference ------------------------------------------------------------------


class SkillOut(ORMModel):
    slug: str
    canonical: str
    category: str
    display_category: str
    tier: str
    description: str | None = None


class RoleSummary(ORMModel):
    slug: str
    title: str
    category: str
    summary: str | None = None
    analyzed_jobs: int = 0


class SourceOut(BaseModel):
    key: str
    name: str
    kind: str
    is_enabled: bool
    notes: str | None = None


# --- Role analysis ----------------------------------------------------------------


class SkillStat(BaseModel):
    skill: SkillOut
    frequency_pct: float
    required_pct: float
    preferred_pct: float
    jobs_mentioning: int
    total_jobs: int
    confidence: str
    rank: int
    priority: str


class CategoryGroup(BaseModel):
    category: str
    label: str
    skills: list[SkillStat]


class DistributionBucket(BaseModel):
    label: str
    count: int
    pct: float


class RoleAnalysis(BaseModel):
    role: RoleSummary
    analyzed_jobs: int
    total_ingested: int
    duplicates_removed: int
    filtered_irrelevant: int
    sources: list[SourceOut]
    last_updated: date | None
    window_start: date | None
    window_end: date | None
    top_skills: list[SkillStat]
    groups: list[CategoryGroup]
    experience_distribution: list[DistributionBucket]
    education_distribution: list[DistributionBucket]
    data_caveat: str


# --- Trends ------------------------------------------------------------------------


class TrendPointOut(BaseModel):
    period: str
    frequency_pct: float
    total_jobs: int
    jobs_mentioning: int


class TrendOut(BaseModel):
    skill: SkillOut
    direction: str
    change_pct: float
    current_pct: float
    slope_per_month: float
    months_observed: int
    points: list[TrendPointOut]


class RoleTrends(BaseModel):
    role: RoleSummary
    emerging: list[TrendOut]
    declining: list[TrendOut]
    stable: list[TrendOut]
    note: str


# --- Roadmap -------------------------------------------------------------------------


class RoadmapItemOut(BaseModel):
    order: int
    skill: SkillOut
    frequency_pct: float
    confidence: str
    priority: str
    reason: str
    prerequisites: list[str]
    already_known: bool


class RoadmapStageOut(BaseModel):
    tier: str
    label: str
    items: list[RoadmapItemOut]


class RoadmapOut(BaseModel):
    role: RoleSummary
    analyzed_jobs: int
    stages: list[RoadmapStageOut]
    note: str


# --- Jobs -------------------------------------------------------------------------


class JobOut(BaseModel):
    id: int
    title: str
    company: str | None
    location: str | None
    employment_type: str | None
    experience: str | None
    min_years: int | None
    max_years: int | None
    education_level: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    salary_period: str | None
    key_skills: list[str]
    source: str
    source_kind: str
    posted_at: date | None
    url: str | None
    is_sample_data: bool


class JobList(BaseModel):
    role: RoleSummary
    total: int
    offset: int
    limit: int
    items: list[JobOut]
    note: str


# --- Ad-hoc analysis ------------------------------------------------------------------


class AnalyzeJobRequest(BaseModel):
    description: str = Field(min_length=40, max_length=40_000)
    title: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    role_slug: str | None = None


class ExtractedSkillOut(BaseModel):
    skill: SkillOut
    requirement_type: str
    mention_count: int
    confidence: float
    evidence: str


class AnalyzeJobResponse(BaseModel):
    title: str
    matched_role: RoleSummary | None
    skills: list[ExtractedSkillOut]
    groups: dict[str, list[ExtractedSkillOut]]
    min_years: int | None
    max_years: int | None
    experience: str
    education_level: str | None
    education_fields: list[str]
    salary_min: int | None
    salary_max: int | None
    comparison_note: str | None


# --- Profile --------------------------------------------------------------------------


class UserSkillIn(BaseModel):
    skill_slug: str
    proficiency: str = Field(default="working", pattern="^(learning|working|strong)$")


class ProfileUpdate(BaseModel):
    skills: list[UserSkillIn] = Field(default_factory=list)
    target_role_slug: str | None = None


class UserSkillOut(BaseModel):
    skill: SkillOut
    proficiency: str


class ProfileOut(BaseModel):
    token: str
    target_role: RoleSummary | None
    skills: list[UserSkillOut]
    privacy_note: str


# --- Skill gap ---------------------------------------------------------------------------


class GapItemOut(BaseModel):
    skill: SkillOut
    frequency_pct: float
    confidence: str
    priority: str
    proficiency: str | None = None


class SkillGapOut(BaseModel):
    role: RoleSummary
    readiness_pct: float
    analyzed_jobs: int
    explanation: str
    disclaimer: str
    high_priority: list[GapItemOut]
    medium_priority: list[GapItemOut]
    low_priority: list[GapItemOut]
    already_strong: list[GapItemOut]


# --- Misc ----------------------------------------------------------------------------------


class HealthOut(BaseModel):
    status: str
    version: str
    database: str
    roles: int
    skills: int
    analyzed_jobs: int
    using_sample_data: bool


class ErrorOut(BaseModel):
    detail: str
