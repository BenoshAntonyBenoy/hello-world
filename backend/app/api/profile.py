"""Anonymous skill profile and gap analysis.

Privacy posture: a profile is an opaque client-generated token plus a list of
skill ids. No email, no name, no password, no third-party identifiers. There is
nothing here to leak that the user did not type in themselves, and
``DELETE /api/profile`` removes all of it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.skillgap import compute_skill_gap
from app.api.common import (
    DbSession,
    get_or_create_user,
    get_profile_token,
    resolve_role,
    role_summary,
    skill_out,
)
from app.models import Role, Skill, User, UserSkill
from app.schemas import (
    GapItemOut,
    ProfileOut,
    ProfileUpdate,
    SkillGapOut,
    UserSkillOut,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])

PRIVACY_NOTE = (
    "This profile is identified only by a token your browser generated. We "
    "store the skills you selected and nothing else — no email, no name, no "
    "password. Deleting it removes every row we hold."
)


def _profile_out(db: Session, user: User) -> ProfileOut:
    rows = db.execute(
        select(UserSkill, Skill)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id == user.id)
        .order_by(Skill.canonical)
    ).all()

    target = (
        db.scalar(select(Role).where(Role.id == user.target_role_id))
        if user.target_role_id
        else None
    )

    return ProfileOut(
        token=user.token,
        target_role=role_summary(db, target) if target else None,
        skills=[
            UserSkillOut(skill=skill_out(skill), proficiency=us.proficiency)
            for us, skill in rows
        ],
        privacy_note=PRIVACY_NOTE,
    )


@router.get("", response_model=ProfileOut, summary="Read the current profile")
def get_profile(
    token: str = Depends(get_profile_token),
    db: Session = DbSession,
) -> ProfileOut:
    user = get_or_create_user(db, token)
    user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return _profile_out(db, user)


@router.post("/skills", response_model=ProfileOut, summary="Replace the skill list")
def set_profile_skills(
    payload: ProfileUpdate,
    token: str = Depends(get_profile_token),
    db: Session = DbSession,
) -> ProfileOut:
    """Full replacement rather than a merge, so the client stays the source of
    truth and removing a skill actually removes it."""
    user = get_or_create_user(db, token)

    slugs = [s.skill_slug for s in payload.skills]
    known = {
        skill.slug: skill
        for skill in db.scalars(select(Skill).where(Skill.slug.in_(slugs))).all()
    }
    unknown = sorted(set(slugs) - set(known))
    if unknown:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown skill slugs: {', '.join(unknown[:10])}",
        )

    if payload.target_role_slug:
        role = resolve_role(db, payload.target_role_slug)
        user.target_role_id = role.id
    elif payload.target_role_slug == "":
        user.target_role_id = None

    db.query(UserSkill).filter(UserSkill.user_id == user.id).delete(
        synchronize_session=False
    )
    seen: set[int] = set()
    for entry in payload.skills:
        skill = known[entry.skill_slug]
        if skill.id in seen:
            continue
        seen.add(skill.id)
        db.add(
            UserSkill(
                user_id=user.id, skill_id=skill.id, proficiency=entry.proficiency
            )
        )

    user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return _profile_out(db, user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete the profile and all its data")
def delete_profile(
    token: str = Depends(get_profile_token),
    db: Session = DbSession,
) -> Response:
    user = db.scalar(select(User).where(User.token == token))
    if user is not None:
        db.delete(user)  # user_skills cascade
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/skill-gap/{role}", response_model=SkillGapOut,
            summary="Compare the profile against a role's demand")
def get_skill_gap(
    role: str,
    token: str = Depends(get_profile_token),
    db: Session = DbSession,
) -> SkillGapOut:
    role_row = resolve_role(db, role)
    user = get_or_create_user(db, token)
    db.commit()

    user_skills = list(
        db.scalars(select(UserSkill).where(UserSkill.user_id == user.id)).all()
    )
    result = compute_skill_gap(db, role_row, user_skills)

    def convert(items) -> list[GapItemOut]:
        return [
            GapItemOut(
                skill=skill_out(i.skill),
                frequency_pct=i.frequency_pct,
                confidence=i.confidence,
                priority=i.priority,
                proficiency=i.proficiency,
            )
            for i in items
        ]

    return SkillGapOut(
        role=role_summary(db, role_row, analyzed=result.total_jobs),
        readiness_pct=result.readiness_pct,
        analyzed_jobs=result.total_jobs,
        explanation=result.explanation,
        disclaimer=result.disclaimer,
        high_priority=convert(result.high_priority),
        medium_priority=convert(result.medium_priority),
        low_priority=convert(result.low_priority),
        already_strong=convert(result.already_strong),
    )
