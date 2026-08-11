"""Skill frequency aggregation.

    frequency = postings mentioning the skill / total relevant postings x 100

The denominator is doing the important work. It counts only postings that
survived relevance filtering and duplicate removal, because counting a listing
reposted eight times as eight data points is how you end up reporting one
company's stack as an industry trend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, JobSkill, Role, RoleSkillStatistic, Skill

# A skill seen in only a handful of postings is noise, however large the corpus.
MIN_SUPPORT = 3


@dataclass
class SkillFrequency:
    skill: Skill
    total_jobs: int
    jobs_mentioning: int
    frequency_pct: float
    required_pct: float
    preferred_pct: float
    confidence: str


def countable_jobs_query(role_id: int):
    """The single definition of "a posting that counts" — used everywhere."""
    return (
        select(Job.id)
        .where(Job.role_id == role_id)
        .where(Job.is_relevant.is_(True))
        .where(Job.is_duplicate.is_(False))
    )


def total_countable(db: Session, role_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(countable_jobs_query(role_id).subquery())
    ) or 0


def rate_confidence(total_jobs: int, jobs_mentioning: int) -> str:
    """Confidence in a single published percentage.

    Driven by sample size, not by how large the percentage is: 90% of 8
    postings is a much weaker claim than 40% of 900.
    """
    if (
        total_jobs >= settings.confidence_high_min_postings
        and jobs_mentioning >= 15
    ):
        return "high"
    if (
        total_jobs >= settings.confidence_medium_min_postings
        and jobs_mentioning >= 5
    ):
        return "medium"
    return "low"


def compute_role_frequencies(db: Session, role: Role) -> list[SkillFrequency]:
    """Aggregate every skill's frequency across one role's countable postings."""
    total = total_countable(db, role.id)
    if total == 0:
        return []

    job_ids = countable_jobs_query(role.id).subquery()

    rows = db.execute(
        select(
            Skill,
            func.count(func.distinct(JobSkill.job_id)).label("mentions"),
            func.sum(
                # Portable boolean-to-int: CASE works on SQLite and Postgres alike.
                case((JobSkill.requirement_type == "required", 1), else_=0)
            ).label("required_count"),
            func.sum(
                case((JobSkill.requirement_type == "preferred", 1), else_=0)
            ).label("preferred_count"),
        )
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .where(JobSkill.job_id.in_(select(job_ids.c.id)))
        .group_by(Skill.id)
        .having(func.count(func.distinct(JobSkill.job_id)) >= MIN_SUPPORT)
    ).all()

    out: list[SkillFrequency] = []
    for skill, mentions, required_count, preferred_count in rows:
        mentions = int(mentions or 0)
        out.append(
            SkillFrequency(
                skill=skill,
                total_jobs=total,
                jobs_mentioning=mentions,
                frequency_pct=round(mentions / total * 100, 1),
                required_pct=round(int(required_count or 0) / total * 100, 1),
                preferred_pct=round(int(preferred_count or 0) / total * 100, 1),
                confidence=rate_confidence(total, mentions),
            )
        )

    out.sort(key=lambda s: (-s.frequency_pct, s.skill.canonical))
    return out


def persist_role_statistics(db: Session, role: Role) -> int:
    """Recompute and replace the stored statistics for one role."""
    frequencies = compute_role_frequencies(db, role)

    db.query(RoleSkillStatistic).filter(
        RoleSkillStatistic.role_id == role.id
    ).delete(synchronize_session=False)

    window = db.execute(
        select(func.min(Job.posted_at), func.max(Job.posted_at))
        .where(Job.role_id == role.id)
        .where(Job.is_relevant.is_(True))
        .where(Job.is_duplicate.is_(False))
    ).one_or_none()
    window_start: date | None = window[0] if window else None
    window_end: date | None = window[1] if window else None

    for rank, freq in enumerate(frequencies, start=1):
        db.add(
            RoleSkillStatistic(
                role_id=role.id,
                skill_id=freq.skill.id,
                total_jobs=freq.total_jobs,
                jobs_mentioning=freq.jobs_mentioning,
                frequency_pct=freq.frequency_pct,
                required_pct=freq.required_pct,
                preferred_pct=freq.preferred_pct,
                confidence=freq.confidence,
                rank=rank,
                window_start=window_start,
                window_end=window_end,
            )
        )

    db.flush()
    return len(frequencies)


def distribution(db: Session, role_id: int, column) -> list[tuple[str, int]]:
    """Counts of a categorical column across countable postings.

    Used for the experience and education charts.
    """
    job_ids = countable_jobs_query(role_id).subquery()
    rows = db.execute(
        select(column, func.count())
        .where(Job.id.in_(select(job_ids.c.id)))
        .group_by(column)
    ).all()
    return [(str(value) if value is not None else "Not specified", int(n)) for value, n in rows]
