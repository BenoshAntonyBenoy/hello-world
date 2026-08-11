"""Time-series trend detection.

A skill's headline percentage says what the market wants *now*. The slope says
where it is going, which is the more useful number when you are choosing what
to spend the next six months learning.

Guardrails, because trend claims are easy to get wrong:

* Months with too few postings are dropped, not smoothed over — a 100% reading
  from three postings is noise wearing a suit.
* A skill needs a minimum number of observed months before it is classified at
  all; everything else is reported as ``insufficient_data``.
* Classification requires both a meaningful slope *and* a meaningful absolute
  change, so a skill wobbling between 3% and 5% is not announced as emerging.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from app.analytics.frequency import countable_jobs_query
from app.models import Job, JobSkill, Role, Skill, SkillTrend

MIN_JOBS_PER_MONTH = 8
MIN_MONTHS = 4

# Direction thresholds, in percentage points.
EMERGING_SLOPE = 0.8       # per month
EMERGING_CHANGE = 6.0      # first third vs last third
DECLINING_SLOPE = -0.6
DECLINING_CHANGE = -4.0

# A fixed percentage-point threshold is wrong on its own: with 15 postings a
# month, a skill sitting flat at 50% will routinely swing ±10pp on sampling
# alone. Any change smaller than this many standard errors is treated as noise,
# so the bar automatically tightens on small corpora and relaxes on large ones.
SIGNIFICANCE_SIGMAS = 2.0


@dataclass
class TrendPoint:
    period: str
    total_jobs: int
    jobs_mentioning: int
    frequency_pct: float


@dataclass
class SkillTrendSummary:
    skill: Skill
    points: list[TrendPoint]
    slope_per_month: float
    change_pct: float
    current_pct: float
    # emerging | declining | stable | insufficient_data
    direction: str

    @property
    def months_observed(self) -> int:
        return len(self.points)


def _period_expr():
    """``YYYY-MM`` from a date column, portable across SQLite and Postgres.

    Both render an ISO date as ``YYYY-MM-DD`` when cast to text, so taking the
    first seven characters avoids dialect-specific date functions.
    """
    return func.substr(func.cast(Job.posted_at, String), 1, 7)


def _linear_slope(values: list[float]) -> float:
    """Least-squares slope over evenly spaced points."""
    n = len(values)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    numerator = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    denominator = sum((i - mean_x) ** 2 for i in range(n))
    return numerator / denominator if denominator else 0.0


def _noise_floor(points: list[TrendPoint], third: int) -> float:
    """Percentage-point change attributable to sampling alone.

    Standard error of the difference between two independent proportions,
    using the pooled rate and the actual posting counts in each window.
    """
    early_points, late_points = points[:third], points[-third:]

    n_early = sum(p.total_jobs for p in early_points)
    n_late = sum(p.total_jobs for p in late_points)
    if n_early == 0 or n_late == 0:
        return 100.0

    mentions = sum(p.jobs_mentioning for p in early_points) + sum(
        p.jobs_mentioning for p in late_points
    )
    pooled = mentions / (n_early + n_late)
    variance = pooled * (1 - pooled) * (1 / n_early + 1 / n_late)
    return SIGNIFICANCE_SIGMAS * math.sqrt(variance) * 100


def _classify(points: list[TrendPoint]) -> tuple[float, float, str]:
    if len(points) < MIN_MONTHS:
        return 0.0, 0.0, "insufficient_data"

    values = [p.frequency_pct for p in points]
    slope = _linear_slope(values)

    third = max(1, len(values) // 3)
    early = sum(values[:third]) / third
    late = sum(values[-third:]) / third
    change = late - early

    floor = _noise_floor(points, third)

    if slope >= EMERGING_SLOPE and change >= max(EMERGING_CHANGE, floor):
        direction = "emerging"
    elif slope <= DECLINING_SLOPE and change <= min(DECLINING_CHANGE, -floor):
        direction = "declining"
    else:
        direction = "stable"

    return round(slope, 3), round(change, 1), direction


def compute_trends(db: Session, role: Role) -> list[SkillTrendSummary]:
    """Monthly frequency series for every skill in a role."""
    job_ids = select(countable_jobs_query(role.id).subquery().c.id)
    period = _period_expr()

    monthly_totals = {
        str(p): int(n)
        for p, n in db.execute(
            select(period, func.count())
            .where(Job.id.in_(job_ids))
            .where(Job.posted_at.is_not(None))
            .group_by(period)
        ).all()
    }
    usable = {p: n for p, n in monthly_totals.items() if n >= MIN_JOBS_PER_MONTH}
    if len(usable) < MIN_MONTHS:
        return []

    rows = db.execute(
        select(Skill, period, func.count(func.distinct(JobSkill.job_id)))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .where(Job.id.in_(job_ids))
        .where(Job.posted_at.is_not(None))
        .group_by(Skill.id, period)
    ).all()

    by_skill: dict[int, tuple[Skill, dict[str, int]]] = {}
    for skill, period_value, mentions in rows:
        key = str(period_value)
        if key not in usable:
            continue
        entry = by_skill.setdefault(skill.id, (skill, {}))
        entry[1][key] = int(mentions)

    summaries: list[SkillTrendSummary] = []
    ordered_periods = sorted(usable)

    for skill, mentions_by_period in by_skill.values():
        points = [
            TrendPoint(
                period=p,
                total_jobs=usable[p],
                jobs_mentioning=mentions_by_period.get(p, 0),
                frequency_pct=round(mentions_by_period.get(p, 0) / usable[p] * 100, 1),
            )
            for p in ordered_periods
        ]
        slope, change, direction = _classify(points)
        summaries.append(
            SkillTrendSummary(
                skill=skill,
                points=points,
                slope_per_month=slope,
                change_pct=change,
                current_pct=points[-1].frequency_pct if points else 0.0,
                direction=direction,
            )
        )

    summaries.sort(key=lambda s: (-s.change_pct, -s.current_pct))
    return summaries


def persist_trends(db: Session, role: Role) -> int:
    """Recompute and replace the stored monthly series for one role."""
    summaries = compute_trends(db, role)

    db.query(SkillTrend).filter(SkillTrend.role_id == role.id).delete(
        synchronize_session=False
    )

    written = 0
    for summary in summaries:
        for point in summary.points:
            db.add(
                SkillTrend(
                    role_id=role.id,
                    skill_id=summary.skill.id,
                    period=point.period,
                    total_jobs=point.total_jobs,
                    jobs_mentioning=point.jobs_mentioning,
                    frequency_pct=point.frequency_pct,
                )
            )
            written += 1

    db.flush()
    return written
