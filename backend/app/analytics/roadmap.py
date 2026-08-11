"""Turn demand statistics into an ordered learning path.

Sorting by frequency alone produces a list, not a plan: it would put PyTorch
above Python because both are common, and tell a beginner to start with
Kubernetes. Two corrections fix that.

**Prerequisites are pulled forward.** If a recommended skill depends on
something the corpus also asks for, the dependency is scheduled first even
where it scores lower.

**Tier bounds the ordering.** Within a stage, demand decides the order. Across
stages, difficulty does.

Every recommendation carries the number it came from, so the user can see why
it is there rather than being asked to trust a ranking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, RoleSkillStatistic, Skill
from app.extraction.taxonomy import BY_CANONICAL, TIER_ORDER, prerequisite_depth

# Categories that belong in a study plan. Soft skills and things like
# "portfolio" matter, but they are not sequenced learning steps.
LEARNABLE = {"language", "framework", "tool", "platform", "concept", "certification"}

DEFAULT_SIZE = 14
STAGE_LABELS = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}


@dataclass
class RoadmapItem:
    order: int
    skill: Skill
    frequency_pct: float
    confidence: str
    priority: str
    reason: str
    prerequisites: list[str] = field(default_factory=list)
    already_known: bool = False


@dataclass
class RoadmapStage:
    tier: str
    label: str
    items: list[RoadmapItem]


def priority_for(frequency_pct: float) -> str:
    if frequency_pct >= 55:
        return "high"
    if frequency_pct >= 30:
        return "medium"
    return "low"


def _display_pct(value: float) -> int:
    """Round half up, matching how the frontend formats the same figure.

    Python's ``:.0f`` rounds half to even, so 36.5 would render as "36" here
    and "37" in the badge sitting next to it. Same number, two answers, in one
    row of the UI.
    """
    return math.floor(value + 0.5)


def _reason(role_title: str, frequency_pct: float, total_jobs: int, confidence: str) -> str:
    base = (
        f"Mentioned in {_display_pct(frequency_pct)}% of the {total_jobs:,} analysed "
        f"{role_title} postings."
    )
    if confidence == "low":
        base += " Sample size is small, so treat this as a weak signal."
    return base


def build_roadmap(
    db: Session,
    role: Role,
    known_skill_ids: set[int] | None = None,
    size: int = DEFAULT_SIZE,
) -> list[RoadmapStage]:
    """Ordered, staged learning path for one role."""
    known = known_skill_ids or set()

    stats = db.execute(
        select(RoleSkillStatistic, Skill)
        .join(Skill, Skill.id == RoleSkillStatistic.skill_id)
        .where(RoleSkillStatistic.role_id == role.id)
        .order_by(RoleSkillStatistic.frequency_pct.desc())
    ).all()
    if not stats:
        return []

    by_canonical = {skill.canonical: (stat, skill) for stat, skill in stats}
    learnable = [(s, k) for s, k in stats if k.category in LEARNABLE]

    selected: dict[str, tuple[RoleSkillStatistic, Skill]] = {}
    for stat, skill in learnable[:size]:
        selected[skill.canonical] = (stat, skill)

    # Pull in prerequisites that the corpus also asks for, even if they fell
    # below the cutoff. A plan that says "learn PyTorch" without Python is
    # worse than useless.
    frontier = list(selected)
    while frontier:
        canonical = frontier.pop()
        definition = BY_CANONICAL.get(canonical)
        if definition is None:
            continue
        for prerequisite in definition.prerequisites:
            if prerequisite in selected:
                continue
            if (entry := by_canonical.get(prerequisite)) is not None:
                selected[prerequisite] = entry
                frontier.append(prerequisite)

    ordered = sorted(
        selected.values(),
        key=lambda pair: (
            TIER_ORDER.get(pair[1].tier, 1),
            prerequisite_depth(pair[1].canonical),
            -pair[0].frequency_pct,
            pair[1].canonical,
        ),
    )

    stages: dict[str, list[RoadmapItem]] = {"beginner": [], "intermediate": [], "advanced": []}
    total_jobs = stats[0][0].total_jobs

    for index, (stat, skill) in enumerate(ordered, start=1):
        definition = BY_CANONICAL.get(skill.canonical)
        prerequisites = [
            p for p in (definition.prerequisites if definition else ()) if p in selected
        ]
        item = RoadmapItem(
            order=index,
            skill=skill,
            frequency_pct=stat.frequency_pct,
            confidence=stat.confidence,
            priority=priority_for(stat.frequency_pct),
            reason=_reason(role.title, stat.frequency_pct, total_jobs, stat.confidence),
            prerequisites=prerequisites,
            already_known=skill.id in known,
        )
        stages.setdefault(skill.tier, stages["intermediate"]).append(item)

    return [
        RoadmapStage(tier=tier, label=STAGE_LABELS[tier], items=items)
        for tier, items in stages.items()
        if items
    ]
