"""Health, search and reference endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import __version__
from app.api.common import DbSession, role_summary, skill_out, source_out
from app.config import settings
from app.models import Job, JobSource, Role, Skill
from app.schemas import HealthOut, RoleSummary, SkillOut, SourceOut

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health", response_model=HealthOut, summary="Service and data status")
def health(db: Session = DbSession) -> HealthOut:
    analyzed = db.scalar(
        select(func.count()).select_from(Job)
        .where(Job.is_relevant.is_(True))
        .where(Job.is_duplicate.is_(False))
    ) or 0
    synthetic = db.scalar(
        select(func.count()).select_from(JobSource).where(JobSource.kind == "synthetic")
    ) or 0

    return HealthOut(
        status="ok",
        version=__version__,
        database="postgresql" if not settings.is_sqlite else "sqlite",
        roles=db.scalar(select(func.count()).select_from(Role)) or 0,
        skills=db.scalar(select(func.count()).select_from(Skill)) or 0,
        analyzed_jobs=analyzed,
        using_sample_data=synthetic > 0,
    )


@router.get("/search", response_model=list[RoleSummary], summary="Search job roles")
def search_roles(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(8, ge=1, le=25),
    db: Session = DbSession,
) -> list[RoleSummary]:
    """Substring match over title and category, ranked by how much of the title
    the query covers. Alias matching is handled by ``resolve_role`` on the
    detail endpoints; here we only need to offer plausible options."""
    needle = f"%{q.strip().lower()}%"
    roles = db.scalars(
        select(Role)
        .where(
            or_(
                func.lower(Role.title).like(needle),
                func.lower(Role.category).like(needle),
                func.lower(Role.slug).like(needle),
            )
        )
        .limit(limit)
    ).all()

    query = q.strip().lower()
    ranked = sorted(
        roles,
        key=lambda r: (
            0 if r.title.lower().startswith(query) else 1,
            len(r.title),
        ),
    )
    return [role_summary(db, role) for role in ranked]


@router.get("/skills", response_model=list[SkillOut], summary="The requirement vocabulary")
def list_skills(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=32),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = DbSession,
) -> list[SkillOut]:
    stmt = select(Skill)
    if q:
        stmt = stmt.where(func.lower(Skill.canonical).like(f"%{q.strip().lower()}%"))
    if category:
        stmt = stmt.where(Skill.category == category)
    skills = db.scalars(stmt.order_by(Skill.canonical).limit(limit)).all()
    return [skill_out(s) for s in skills]


@router.get("/sources", response_model=list[SourceOut], summary="Where the data came from")
def list_sources(db: Session = DbSession) -> list[SourceOut]:
    sources = db.scalars(select(JobSource).order_by(JobSource.name)).all()
    return [source_out(s) for s in sources]
