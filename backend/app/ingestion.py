"""The ingestion pipeline.

    connector -> normalize -> dedupe -> relevance -> extract -> persist -> aggregate

This is the only module that knows about all the pieces at once. Everything it
calls is independently testable, and the connector on the left-hand side is
interchangeable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.frequency import persist_role_statistics
from app.analytics.trends import persist_trends
from app.connectors.base import JobDataConnector, RawPosting
from app.data.roles import ROLE_PROFILES, validate_catalog
from app.extraction import extract
from app.extraction.dedupe import (
    DuplicateIndex,
    RELEVANCE_THRESHOLD,
    from_hex,
    relevance_score,
    to_hex,
)
from app.extraction.taxonomy import CATALOG
from app.models import Company, Job, JobSkill, JobSource, Role, Skill

log = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    source_key: str
    fetched: int = 0
    stored: int = 0
    exact_reposts: int = 0
    near_duplicates: int = 0
    irrelevant: int = 0
    unmapped_role: int = 0
    skills_linked: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def duplicates(self) -> int:
        return self.exact_reposts + self.near_duplicates

    def summary(self) -> str:
        return (
            f"{self.source_key}: fetched {self.fetched}, stored {self.stored}, "
            f"reposts {self.exact_reposts}, near-dupes {self.near_duplicates}, "
            f"irrelevant {self.irrelevant}, unmapped {self.unmapped_role}, "
            f"skill links {self.skills_linked}"
        )


# --- Reference data -------------------------------------------------------------


def ensure_reference_data(db: Session) -> None:
    """Upsert the taxonomy, role catalogue and source descriptors.

    Safe to call repeatedly; it reconciles rather than duplicating.
    """
    problems = validate_catalog()
    if problems:
        raise ValueError(
            "Role profiles reference skills missing from the taxonomy:\n  "
            + "\n  ".join(problems)
        )

    existing_skills = {s.slug: s for s in db.scalars(select(Skill)).all()}
    for definition in CATALOG:
        row = existing_skills.get(definition.slug)
        if row is None:
            db.add(
                Skill(
                    slug=definition.slug,
                    canonical=definition.canonical,
                    category=definition.category,
                    tier=definition.tier,
                    aliases=list(definition.aliases),
                    prerequisites=list(definition.prerequisites),
                    description=definition.description or None,
                )
            )
        else:
            row.canonical = definition.canonical
            row.category = definition.category
            row.tier = definition.tier
            row.aliases = list(definition.aliases)
            row.prerequisites = list(definition.prerequisites)
            row.description = definition.description or None

    existing_roles = {r.slug: r for r in db.scalars(select(Role)).all()}
    for profile in ROLE_PROFILES:
        row = existing_roles.get(profile.slug)
        if row is None:
            db.add(
                Role(
                    slug=profile.slug,
                    title=profile.title,
                    category=profile.category,
                    summary=profile.summary,
                    aliases=list(profile.aliases),
                )
            )
        else:
            row.title = profile.title
            row.category = profile.category
            row.summary = profile.summary
            row.aliases = list(profile.aliases)

    db.flush()


def ensure_source(db: Session, connector: JobDataConnector) -> JobSource:
    descriptor = connector.descriptor
    source = db.scalar(select(JobSource).where(JobSource.key == descriptor.key))
    if source is None:
        source = JobSource(key=descriptor.key)
        db.add(source)
    source.name = descriptor.name
    source.kind = descriptor.kind
    source.base_url = descriptor.base_url
    source.terms_url = descriptor.terms_url
    source.requires_license = descriptor.requires_license
    source.notes = descriptor.notes
    source.is_enabled = True
    db.flush()
    return source


def _get_company(db: Session, cache: dict[str, Company], name: str | None) -> Company | None:
    if not name:
        return None
    key = " ".join(name.split()).lower()
    if key in cache:
        return cache[key]
    company = db.scalar(select(Company).where(Company.normalized_name == key))
    if company is None:
        company = Company(name=name.strip(), normalized_name=key)
        db.add(company)
        db.flush()
    cache[key] = company
    return company


# --- Ingestion -------------------------------------------------------------------


def ingest(
    db: Session,
    connector: JobDataConnector,
    role_slugs: list[str] | None = None,
    limit: int | None = None,
) -> IngestionReport:
    """Pull from one connector and persist everything that survives filtering."""
    report = IngestionReport(source_key=connector.key)
    source = ensure_source(db, connector)

    roles_by_slug = {r.slug: r for r in db.scalars(select(Role)).all()}
    profiles_by_slug = {p.slug: p for p in ROLE_PROFILES}
    skills_by_canonical = {s.canonical: s for s in db.scalars(select(Skill)).all()}
    company_cache: dict[str, Company] = {}

    # Duplicate detection is per-source: the same listing appearing on two
    # different boards is genuinely two observations of one vacancy, and is
    # handled at query time rather than by dropping one at ingest.
    # Fingerprints are persisted so a second ingestion run can pick up where
    # the first left off instead of re-reading every stored posting.
    index = DuplicateIndex()
    for job_id, content, fingerprint in db.execute(
        select(Job.id, Job.content_hash, Job.fingerprint)
        .where(Job.source_id == source.id)
        .where(Job.is_duplicate.is_(False))
    ).all():
        index.add(content, from_hex(fingerprint), job_id)

    for posting in connector.fetch(role_slugs=role_slugs, limit=limit):
        report.fetched += 1
        try:
            # A SAVEPOINT per posting: one malformed record rolls back only
            # itself. Without this, a single integrity error poisons the
            # session and every subsequent posting in the run is lost.
            with db.begin_nested():
                stored = _ingest_one(
                    db, source, posting, roles_by_slug, profiles_by_slug,
                    skills_by_canonical, company_cache, index, report,
                )
            if stored:
                report.stored += 1
        except Exception as exc:
            log.warning("Skipped posting %s: %s", posting.external_id, exc)
            report.errors.append(f"{posting.external_id}: {exc}")

    db.commit()
    return report


def _ingest_one(
    db: Session,
    source: JobSource,
    posting: RawPosting,
    roles_by_slug: dict[str, Role],
    profiles_by_slug: dict,
    skills_by_canonical: dict[str, Skill],
    company_cache: dict[str, Company],
    index: DuplicateIndex,
    report: IngestionReport,
) -> bool:
    role = roles_by_slug.get(posting.role_hint) if posting.role_hint else None
    if role is None:
        report.unmapped_role += 1
        return False

    result = extract(posting.description)

    # An exact repost is the same document arriving twice. There is nothing new
    # to record, and storing it would collide with uq_jobs_source_hash anyway.
    if index.find_exact(result.content_hash) is not None:
        report.exact_reposts += 1
        return False

    # A near-duplicate is a distinct document describing the same vacancy
    # (a relist with one line changed). Worth keeping for provenance, but
    # excluded from every statistic by the is_duplicate flag.
    near_of = index.find_near(result.fingerprint)
    if near_of is not None:
        report.near_duplicates += 1
        db.add(
            Job(
                source_id=source.id,
                role_id=role.id,
                company_id=None,
                external_id=posting.external_id,
                title=posting.title,
                raw_title=posting.title,
                description_raw=posting.description,
                description_normalized=result.normalized_text,
                content_hash=result.content_hash,
                fingerprint=to_hex(result.fingerprint),
                posted_at=posting.posted_at,
                is_duplicate=True,
                duplicate_of_id=near_of,
                is_relevant=True,
                relevance_score=0.0,
            )
        )
        db.flush()
        # Registered so a third copy matches this one too, but only under its
        # own hash — the canonical job id stays the original.
        index.add(result.content_hash, result.fingerprint, near_of)
        return True

    profile = profiles_by_slug.get(role.slug)
    core_names = set(profile.core) if profile else set()
    core_found = len(result.canonical_names() & core_names)

    score = relevance_score(
        title=posting.title,
        text=result.normalized_text,
        role_title=role.title,
        role_aliases=tuple(role.aliases or ()),
        core_skills_found=core_found,
    )
    is_relevant = score >= RELEVANCE_THRESHOLD
    if not is_relevant:
        report.irrelevant += 1

    company = _get_company(db, company_cache, posting.company)

    job = Job(
        source_id=source.id,
        company_id=company.id if company else None,
        role_id=role.id,
        external_id=posting.external_id,
        title=posting.title,
        raw_title=posting.title,
        location=posting.location,
        country=posting.country,
        employment_type=posting.employment_type,
        description_raw=posting.description,
        description_normalized=result.normalized_text,
        content_hash=result.content_hash,
        fingerprint=to_hex(result.fingerprint),
        seniority=result.experience_bucket,
        min_years=result.min_years,
        max_years=result.max_years,
        education_level=result.education_level,
        education_fields=result.education_fields,
        salary_min=result.salary_min,
        salary_max=result.salary_max,
        salary_currency=result.salary_currency,
        salary_period=result.salary_period,
        url=posting.url,
        posted_at=posting.posted_at,
        is_relevant=is_relevant,
        relevance_score=score,
        is_duplicate=False,
    )
    db.add(job)
    db.flush()

    index.add(result.content_hash, result.fingerprint, job.id)

    for extracted in result.skills:
        skill = skills_by_canonical.get(extracted.canonical)
        if skill is None:
            continue
        db.add(
            JobSkill(
                job_id=job.id,
                skill_id=skill.id,
                requirement_type=extracted.requirement_type,
                mention_count=extracted.mention_count,
                confidence=extracted.confidence,
                evidence=extracted.evidence[:500],
            )
        )
        report.skills_linked += 1

    return True


def recompute_analytics(db: Session) -> dict[str, dict[str, int]]:
    """Rebuild statistics and trend series for every role."""
    out: dict[str, dict[str, int]] = {}
    for role in db.scalars(select(Role)).all():
        stats = persist_role_statistics(db, role)
        trends = persist_trends(db, role)
        out[role.slug] = {"skills": stats, "trend_points": trends}
    db.commit()
    return out
