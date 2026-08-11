"""Analytics: frequency, trends, roadmaps and skill-gap scoring."""

from app.analytics.frequency import (
    SkillFrequency,
    compute_role_frequencies,
    persist_role_statistics,
)
from app.analytics.roadmap import RoadmapItem, RoadmapStage, build_roadmap
from app.analytics.skillgap import SkillGapResult, compute_skill_gap
from app.analytics.trends import SkillTrendSummary, compute_trends, persist_trends

__all__ = [
    "RoadmapItem",
    "RoadmapStage",
    "SkillFrequency",
    "SkillGapResult",
    "SkillTrendSummary",
    "build_roadmap",
    "compute_role_frequencies",
    "compute_skill_gap",
    "compute_trends",
    "persist_role_statistics",
    "persist_trends",
]
