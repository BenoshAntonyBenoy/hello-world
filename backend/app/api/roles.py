"""Role analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.frequency import distribution, total_countable
from app.analytics.roadmap import build_roadmap
from app.analytics.trends import compute_trends
from app.api.common import (
    DbSession,
    caveat_for,
    resolve_role,
    role_summary,
    skill_out,
    source_out,
    sources_for_role,
    stat_out,
)
from app.extraction.taxonomy import CATEGORY_LABELS
from app.models import Job, JobSkill, Role, RoleSkillStatistic, Skill, User, UserSkill
from app.schemas import (
    CategoryGroup,
    DistributionBucket,
    JobList,
    JobOut,
    RoadmapItemOut,
    RoadmapOut,
    RoadmapStageOut,
    RoleAnalysis,
    RoleSummary,
    RoleTrends,
    TrendOut,
    TrendPointOut,
)

router = APIRouter(prefix="/api/roles", tags=["roles"])

# Order categories appear in the dashboard.
CATEGORY_ORDER = [
    "Technical Skills",
    "Tools & Technologies",
    "Soft Skills",
    "Certifications",
    "Other Requirements",
]


def _buckets(rows: list[tuple[str, int]]) -> list[DistributionBucket]:
    total = sum(count for _, count in rows) or 1
    out = [
        DistributionBucket(label=label, count=count, pct=round(count / total * 100, 1))
        for label, count in rows
    ]
    out.sort(key=lambda b: -b.count)
    return out


@router.get("", response_model=list[RoleSummary], summary="List analysed roles")
def list_roles(db: Session = DbSession) -> list[RoleSummary]:
    counts = dict(
        db.execute(
            select(Job.role_id, func.count())
            .where(Job.is_relevant.is_(True))
            .where(Job.is_duplicate.is_(False))
            .group_by(Job.role_id)
        ).all()
    )
    roles = db.scalars(select(Role).order_by(Role.title)).all()
    return [
        role_summary(db, role, analyzed=int(counts.get(role.id, 0))) for role in roles
    ]


@router.get("/{role}", response_model=RoleAnalysis, summary="Full analysis for a role")
def get_role(role: str, db: Session = DbSession) -> RoleAnalysis:
    row = resolve_role(db, role)

    analyzed = total_countable(db, row.id)
    total_ingested = db.scalar(
        select(func.count()).select_from(Job).where(Job.role_id == row.id)
    ) or 0
    duplicates = db.scalar(
        select(func.count()).select_from(Job)
        .where(Job.role_id == row.id).where(Job.is_duplicate.is_(True))
    ) or 0
    irrelevant = db.scalar(
        select(func.count()).select_from(Job)
        .where(Job.role_id == row.id)
        .where(Job.is_relevant.is_(False))
        .where(Job.is_duplicate.is_(False))
    ) or 0

    stats = db.execute(
        select(RoleSkillStatistic, Skill)
        .join(Skill, Skill.id == RoleSkillStatistic.skill_id)
        .where(RoleSkillStatistic.role_id == row.id)
        .order_by(RoleSkillStatistic.frequency_pct.desc())
    ).all()
    all_stats = [stat_out(stat, skill) for stat, skill in stats]

    grouped: dict[str, list] = {}
    for item in all_stats:
        grouped.setdefault(item.skill.display_category, []).append(item)
    groups = [
        CategoryGroup(
            category=label,
            label=label,
            skills=grouped[label],
        )
        for label in CATEGORY_ORDER
        if grouped.get(label)
    ]

    sources = sources_for_role(db, row.id)
    window = stats[0][0] if stats else None
    last_posted = db.scalar(
        select(func.max(Job.posted_at))
        .where(Job.role_id == row.id)
        .where(Job.is_duplicate.is_(False))
    )

    return RoleAnalysis(
        role=role_summary(db, row, analyzed=analyzed),
        analyzed_jobs=analyzed,
        total_ingested=total_ingested,
        duplicates_removed=duplicates,
        filtered_irrelevant=irrelevant,
        sources=[source_out(s) for s in sources],
        last_updated=last_posted,
        window_start=window.window_start if window else None,
        window_end=window.window_end if window else None,
        top_skills=all_stats[:12],
        groups=groups,
        experience_distribution=_buckets(distribution(db, row.id, Job.seniority)),
        education_distribution=_buckets(distribution(db, row.id, Job.education_level)),
        data_caveat=caveat_for(sources),
    )


@router.get("/{role}/skills", response_model=list[CategoryGroup],
            summary="Every extracted requirement, grouped by category")
def get_role_skills(
    role: str,
    min_frequency: float = Query(0.0, ge=0, le=100),
    db: Session = DbSession,
) -> list[CategoryGroup]:
    row = resolve_role(db, role)
    stats = db.execute(
        select(RoleSkillStatistic, Skill)
        .join(Skill, Skill.id == RoleSkillStatistic.skill_id)
        .where(RoleSkillStatistic.role_id == row.id)
        .where(RoleSkillStatistic.frequency_pct >= min_frequency)
        .order_by(RoleSkillStatistic.frequency_pct.desc())
    ).all()

    grouped: dict[str, list] = {}
    for stat, skill in stats:
        item = stat_out(stat, skill)
        grouped.setdefault(item.skill.display_category, []).append(item)

    return [
        CategoryGroup(category=label, label=label, skills=grouped[label])
        for label in CATEGORY_ORDER
        if grouped.get(label)
    ]


@router.get("/{role}/trends", response_model=RoleTrends, summary="How demand is shifting")
def get_role_trends(
    role: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = DbSession,
) -> RoleTrends:
    row = resolve_role(db, role)
    summaries = compute_trends(db, row)

    def convert(items) -> list[TrendOut]:
        return [
            TrendOut(
                skill=skill_out(s.skill),
                direction=s.direction,
                change_pct=s.change_pct,
                current_pct=s.current_pct,
                slope_per_month=s.slope_per_month,
                months_observed=s.months_observed,
                points=[
                    TrendPointOut(
                        period=p.period,
                        frequency_pct=p.frequency_pct,
                        total_jobs=p.total_jobs,
                        jobs_mentioning=p.jobs_mentioning,
                    )
                    for p in s.points
                ],
            )
            for s in items
        ]

    emerging = [s for s in summaries if s.direction == "emerging"][:limit]
    declining = [s for s in summaries if s.direction == "declining"][:limit]
    stable = sorted(
        (s for s in summaries if s.direction == "stable"),
        key=lambda s: -s.current_pct,
    )[:limit]

    note = (
        "A skill is only labelled emerging or declining when the change exceeds "
        "two standard errors for the number of postings observed, so small "
        "month-to-month swings are reported as stable rather than as a trend."
    )
    if not summaries:
        note = (
            "Not enough monthly history for this role yet. Trends need at least "
            "four months with a workable number of postings in each."
        )

    return RoleTrends(
        role=role_summary(db, row),
        emerging=convert(emerging),
        declining=convert(declining),
        stable=convert(stable),
        note=note,
    )


@router.get("/{role}/roadmap", response_model=RoadmapOut,
            summary="Learning path ordered by demand and prerequisites")
def get_role_roadmap(
    role: str,
    profile_token: str | None = Query(default=None, description="Optional anonymous profile token"),
    db: Session = DbSession,
) -> RoadmapOut:
    row = resolve_role(db, role)

    known: set[int] = set()
    if profile_token:
        user = db.scalar(select(User).where(User.token == profile_token))
        if user is not None:
            known = {
                us.skill_id
                for us in db.scalars(
                    select(UserSkill).where(UserSkill.user_id == user.id)
                ).all()
            }

    stages = build_roadmap(db, row, known_skill_ids=known)
    analyzed = total_countable(db, row.id)

    return RoadmapOut(
        role=role_summary(db, row, analyzed=analyzed),
        analyzed_jobs=analyzed,
        stages=[
            RoadmapStageOut(
                tier=stage.tier,
                label=stage.label,
                items=[
                    RoadmapItemOut(
                        order=item.order,
                        skill=skill_out(item.skill),
                        frequency_pct=item.frequency_pct,
                        confidence=item.confidence,
                        priority=item.priority,
                        reason=item.reason,
                        prerequisites=item.prerequisites,
                        already_known=item.already_known,
                    )
                    for item in stage.items
                ],
            )
            for stage in stages
        ],
        note=(
            "Ordered by how often each skill appears in analysed postings, with "
            "prerequisites scheduled before the skills that depend on them. "
            "It is a prioritisation aid, not a guarantee of any outcome."
        ),
    )


@router.get("/{role}/jobs", response_model=JobList, summary="Postings behind the analysis")
def get_role_jobs(
    role: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = DbSession,
) -> JobList:
    row = resolve_role(db, role)

    base = (
        select(Job)
        .where(Job.role_id == row.id)
        .where(Job.is_relevant.is_(True))
        .where(Job.is_duplicate.is_(False))
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    jobs = db.scalars(
        base.order_by(Job.posted_at.desc().nullslast(), Job.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items: list[JobOut] = []
    for job in jobs:
        top_skills = db.execute(
            select(Skill.canonical)
            .join(JobSkill, JobSkill.skill_id == Skill.id)
            .where(JobSkill.job_id == job.id)
            .where(JobSkill.requirement_type == "required")
            .order_by(JobSkill.confidence.desc())
            .limit(6)
        ).scalars().all()

        items.append(
            JobOut(
                id=job.id,
                title=job.title,
                company=job.company.name if job.company else None,
                location=job.location,
                employment_type=job.employment_type,
                experience=job.seniority,
                min_years=job.min_years,
                max_years=job.max_years,
                education_level=job.education_level,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_currency=job.salary_currency,
                salary_period=job.salary_period,
                key_skills=list(top_skills),
                source=job.source.name,
                source_kind=job.source.kind,
                posted_at=job.posted_at,
                url=job.url,
                is_sample_data=job.source.kind == "synthetic",
            )
        )

    sources = sources_for_role(db, row.id)
    return JobList(
        role=role_summary(db, row),
        total=total,
        offset=offset,
        limit=limit,
        items=items,
        note=caveat_for(sources),
    )
