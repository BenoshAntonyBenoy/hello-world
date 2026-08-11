"""Shared dependencies and ORM-to-schema conversion."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.frequency import total_countable
from app.analytics.roadmap import priority_for
from app.data.roles import find_role as find_profile
from app.database import get_db
from app.extraction.taxonomy import CATEGORY_LABELS
from app.models import Job, JobSource, Role, RoleSkillStatistic, Skill, User
from app.schemas import RoleSummary, SkillOut, SkillStat, SourceOut

SAMPLE_DATA_CAVEAT = (
    "These figures are computed from a synthetic sample corpus generated for "
    "development. They demonstrate the analysis pipeline and are not evidence "
    "about the real job market."
)

LIVE_DATA_CAVEAT = (
    "Figures reflect postings collected from the listed sources over the stated "
    "window. Coverage is partial and varies by role and region."
)


# --- Lookups -----------------------------------------------------------------


def resolve_role(db: Session, identifier: str) -> Role:
    """Resolve a slug, exact title or loose free-text query to a Role."""
    needle = (identifier or "").strip()
    if not needle:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No role specified")

    role = db.scalar(select(Role).where(Role.slug == needle.lower()))
    if role is not None:
        return role

    role = db.scalar(select(Role).where(func.lower(Role.title) == needle.lower()))
    if role is not None:
        return role

    if (profile := find_profile(needle)) is not None:
        role = db.scalar(select(Role).where(Role.slug == profile.slug))
        if role is not None:
            return role

    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"No analysed role matches {identifier!r}. Try GET /api/roles for the list.",
    )


def get_profile_token(
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
) -> str:
    """Anonymous profile identity.

    The client generates an opaque token and stores it locally. No email, no
    password, no account — deleting the token is deleting the profile.
    """
    token = (x_profile_token or "").strip()
    if not token or len(token) < 8 or len(token) > 64:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Missing or malformed X-Profile-Token header (8–64 characters).",
        )
    return token


def get_or_create_user(db: Session, token: str) -> User:
    user = db.scalar(select(User).where(User.token == token))
    if user is None:
        user = User(token=token)
        db.add(user)
        db.flush()
    return user


DbSession = Depends(get_db)


# --- Conversion ---------------------------------------------------------------


def skill_out(skill: Skill) -> SkillOut:
    return SkillOut(
        slug=skill.slug,
        canonical=skill.canonical,
        category=skill.category,
        display_category=CATEGORY_LABELS.get(skill.category, "Other Requirements"),
        tier=skill.tier,
        description=skill.description,
    )


def role_summary(db: Session, role: Role, analyzed: int | None = None) -> RoleSummary:
    return RoleSummary(
        slug=role.slug,
        title=role.title,
        category=role.category,
        summary=role.summary,
        analyzed_jobs=total_countable(db, role.id) if analyzed is None else analyzed,
    )


def stat_out(stat: RoleSkillStatistic, skill: Skill) -> SkillStat:
    return SkillStat(
        skill=skill_out(skill),
        frequency_pct=stat.frequency_pct,
        required_pct=stat.required_pct,
        preferred_pct=stat.preferred_pct,
        jobs_mentioning=stat.jobs_mentioning,
        total_jobs=stat.total_jobs,
        confidence=stat.confidence,
        rank=stat.rank,
        priority=priority_for(stat.frequency_pct),
    )


def source_out(source: JobSource) -> SourceOut:
    return SourceOut(
        key=source.key,
        name=source.name,
        kind=source.kind,
        is_enabled=source.is_enabled,
        notes=source.notes,
    )


def sources_for_role(db: Session, role_id: int) -> list[JobSource]:
    return list(
        db.scalars(
            select(JobSource)
            .join(Job, Job.source_id == JobSource.id)
            .where(Job.role_id == role_id)
            .distinct()
        ).all()
    )


def caveat_for(sources: list[JobSource]) -> str:
    """Sample-data warning wherever any contributing source is synthetic."""
    if any(s.kind == "synthetic" for s in sources):
        return SAMPLE_DATA_CAVEAT
    return LIVE_DATA_CAVEAT
