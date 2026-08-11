"""Compare a personal skill profile against a role's demand.

The readiness score is **demand-weighted coverage**: of all the demand signal
in this role's postings, how much of it does the user already cover?

    readiness = Σ frequency(skills the user has) / Σ frequency(all skills) × 100

Weighting by frequency is the whole point. Counting skills equally would let
someone claim readiness by knowing six rare tools while missing SQL.

What this number is **not**: a probability of being hired. It says nothing
about interview performance, portfolio quality, referrals, or whether anyone
is hiring at all. Every response carries that caveat, and the UI shows it —
a career tool that implies a guarantee is doing real harm to someone making a
real decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, RoleSkillStatistic, Skill, UserSkill

# How much credit a self-reported proficiency earns.
PROFICIENCY_WEIGHT = {"strong": 1.0, "working": 0.85, "learning": 0.45}

# Only skills above this frequency shape the score; the long tail of rare
# mentions would otherwise dominate the denominator.
FREQUENCY_FLOOR = 8.0

DISCLAIMER = (
    "Readiness measures how much of this role's commonly requested skill set "
    "you currently cover, based on analysed postings. It is not a prediction "
    "of hiring outcomes and does not account for interviews, portfolio, "
    "referrals or current openings."
)


@dataclass
class GapItem:
    skill: Skill
    frequency_pct: float
    confidence: str
    priority: str
    proficiency: str | None = None


@dataclass
class SkillGapResult:
    role: Role
    readiness_pct: float
    total_jobs: int
    covered_weight: float
    total_weight: float
    high_priority: list[GapItem] = field(default_factory=list)
    medium_priority: list[GapItem] = field(default_factory=list)
    low_priority: list[GapItem] = field(default_factory=list)
    already_strong: list[GapItem] = field(default_factory=list)
    explanation: str = ""
    disclaimer: str = DISCLAIMER


def _priority(frequency_pct: float) -> str:
    if frequency_pct >= 50:
        return "high"
    if frequency_pct >= 25:
        return "medium"
    return "low"


def compute_skill_gap(
    db: Session,
    role: Role,
    user_skills: list[UserSkill],
) -> SkillGapResult:
    """Demand-weighted gap analysis for one user against one role."""
    stats = db.execute(
        select(RoleSkillStatistic, Skill)
        .join(Skill, Skill.id == RoleSkillStatistic.skill_id)
        .where(RoleSkillStatistic.role_id == role.id)
        .where(RoleSkillStatistic.frequency_pct >= FREQUENCY_FLOOR)
        .order_by(RoleSkillStatistic.frequency_pct.desc())
    ).all()

    if not stats:
        return SkillGapResult(
            role=role,
            readiness_pct=0.0,
            total_jobs=0,
            covered_weight=0.0,
            total_weight=0.0,
            explanation=(
                f"No analysed postings for {role.title} yet, so there is nothing "
                "to compare against."
            ),
        )

    proficiency_by_skill = {us.skill_id: us.proficiency for us in user_skills}
    total_jobs = stats[0][0].total_jobs

    total_weight = 0.0
    covered_weight = 0.0
    result = SkillGapResult(
        role=role,
        readiness_pct=0.0,
        total_jobs=total_jobs,
        covered_weight=0.0,
        total_weight=0.0,
    )

    for stat, skill in stats:
        weight = stat.frequency_pct
        total_weight += weight
        priority = _priority(stat.frequency_pct)
        proficiency = proficiency_by_skill.get(skill.id)

        item = GapItem(
            skill=skill,
            frequency_pct=stat.frequency_pct,
            confidence=stat.confidence,
            priority=priority,
            proficiency=proficiency,
        )

        if proficiency:
            covered_weight += weight * PROFICIENCY_WEIGHT.get(proficiency, 0.85)
            result.already_strong.append(item)
        elif priority == "high":
            result.high_priority.append(item)
        elif priority == "medium":
            result.medium_priority.append(item)
        else:
            result.low_priority.append(item)

    readiness = (covered_weight / total_weight * 100) if total_weight else 0.0

    result.readiness_pct = round(readiness, 1)
    result.covered_weight = round(covered_weight, 1)
    result.total_weight = round(total_weight, 1)
    result.already_strong.sort(key=lambda i: -i.frequency_pct)
    result.explanation = _explain(result)
    return result


def _explain(result: SkillGapResult) -> str:
    covered = len(result.already_strong)
    missing = (
        len(result.high_priority)
        + len(result.medium_priority)
        + len(result.low_priority)
    )
    parts = [
        f"You cover {covered} of the {covered + missing} skills commonly "
        f"requested for {result.role.title}, weighted by how often each one "
        f"appears across {result.total_jobs:,} analysed postings."
    ]
    if result.high_priority:
        names = ", ".join(i.skill.canonical for i in result.high_priority[:3])
        parts.append(
            f"The largest gaps are {names} — each appears in at least half of "
            "these postings."
        )
    elif result.medium_priority:
        parts.append(
            "No high-frequency skills are missing; the remaining gaps are in "
            "moderately requested areas."
        )
    else:
        parts.append("You cover every frequently requested skill for this role.")
    return " ".join(parts)
