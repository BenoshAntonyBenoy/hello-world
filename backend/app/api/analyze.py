"""Ad-hoc analysis of a job description the user supplies."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import DbSession, role_summary, skill_out
from app.connectors.user_submitted import user_submitted
from app.data.roles import find_role as find_profile
from app.extraction import extract
from app.models import Role, RoleSkillStatistic, Skill
from app.schemas import AnalyzeJobRequest, AnalyzeJobResponse, ExtractedSkillOut

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze-job", response_model=AnalyzeJobResponse,
             summary="Extract requirements from a pasted job description")
def analyze_job(payload: AnalyzeJobRequest, db: Session = DbSession) -> AnalyzeJobResponse:
    """Run the same pipeline used for ingestion over one supplied posting.

    The submission is buffered in memory only. It is deliberately not merged
    into published role statistics — otherwise anyone could move the numbers by
    pasting the same text repeatedly.
    """
    title = (payload.title or "Pasted job description").strip()

    user_submitted.submit(
        description=payload.description,
        title=title,
        company=payload.company,
        role_hint=payload.role_slug,
    )

    result = extract(payload.description)

    # Work out which role this looks like, from the explicit hint, the title,
    # or failing that the first line of the description.
    matched: Role | None = None
    for candidate in (payload.role_slug, title, payload.description[:120]):
        if not candidate:
            continue
        if (profile := find_profile(candidate)) is not None:
            matched = db.scalar(select(Role).where(Role.slug == profile.slug))
            if matched is not None:
                break

    skills_by_canonical = {
        s.canonical: s for s in db.scalars(select(Skill)).all()
    }

    items: list[ExtractedSkillOut] = []
    for extracted in result.skills:
        skill_row = skills_by_canonical.get(extracted.canonical)
        if skill_row is None:
            continue
        items.append(
            ExtractedSkillOut(
                skill=skill_out(skill_row),
                requirement_type=extracted.requirement_type,
                mention_count=extracted.mention_count,
                confidence=extracted.confidence,
                evidence=extracted.evidence,
            )
        )

    groups: dict[str, list[ExtractedSkillOut]] = {}
    for item in items:
        groups.setdefault(item.skill.display_category, []).append(item)

    comparison_note: str | None = None
    if matched is not None and items:
        found = {i.skill.canonical for i in items}
        common = db.execute(
            select(Skill.canonical, RoleSkillStatistic.frequency_pct)
            .join(RoleSkillStatistic, RoleSkillStatistic.skill_id == Skill.id)
            .where(RoleSkillStatistic.role_id == matched.id)
            .where(RoleSkillStatistic.frequency_pct >= 40)
            .order_by(RoleSkillStatistic.frequency_pct.desc())
        ).all()
        missing = [name for name, _ in common if name not in found]
        if missing:
            comparison_note = (
                f"Compared with other {matched.title} postings we have analysed, "
                f"this one does not mention: {', '.join(missing[:6])}. That may "
                "mean the role is scoped differently, or simply that the posting "
                "is less detailed."
            )
        else:
            comparison_note = (
                f"This posting covers every requirement that appears in at least "
                f"40% of the {matched.title} postings we have analysed."
            )

    return AnalyzeJobResponse(
        title=title,
        matched_role=role_summary(db, matched) if matched else None,
        skills=items,
        groups=groups,
        min_years=result.min_years,
        max_years=result.max_years,
        experience=result.experience_bucket,
        education_level=result.education_level,
        education_fields=result.education_fields,
        salary_min=result.salary_min,
        salary_max=result.salary_max,
        comparison_note=comparison_note,
    )
