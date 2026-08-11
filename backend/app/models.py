"""SQLAlchemy ORM models.

Table set matches the schema in the product spec:
    jobs, companies, job_sources, skills, job_skills, roles,
    role_skill_statistics, users, user_skills, skill_trends
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobSource(Base):
    """A place job postings come from.

    ``kind`` records *how* we are legally allowed to obtain the data, so the
    compliance posture of every posting is auditable from the row itself.
    """

    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    # api | licensed_dataset | public_feed | user_submitted | synthetic
    kind: Mapped[str] = mapped_column(String(32))
    base_url: Mapped[str | None] = mapped_column(String(512))
    terms_url: Mapped[str | None] = mapped_column(String(512))
    requires_license: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    jobs: Mapped[list[Job]] = relationship(back_populates="source")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    normalized_name: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    jobs: Mapped[list[Job]] = relationship(back_populates="company")


class Role(Base):
    """A canonical job role users can search for."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    jobs: Mapped[list[Job]] = relationship(back_populates="role")
    statistics: Mapped[list[RoleSkillStatistic]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class Skill(Base):
    """A canonical requirement: skill, tool, degree, certification, etc."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    canonical: Mapped[str] = mapped_column(String(128))
    # language | framework | tool | platform | concept | soft | certification
    # | education | experience | other
    category: Mapped[str] = mapped_column(String(32), index=True)
    # beginner | intermediate | advanced
    tier: Mapped[str] = mapped_column(String(16), default="intermediate")
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    learn_url: Mapped[str | None] = mapped_column(String(512))

    job_links: Mapped[list[JobSkill]] = relationship(back_populates="skill")


class Job(Base):
    """A single normalized job posting."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="uq_jobs_source_hash"),
        Index("ix_jobs_role_posted", "role_id", "posted_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("job_sources.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), index=True)

    external_id: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(256))
    raw_title: Mapped[str] = mapped_column(String(256))
    location: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(64))
    employment_type: Mapped[str | None] = mapped_column(String(48))

    description_raw: Mapped[str] = mapped_column(Text)
    description_normalized: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    # 64-bit simhash as hex. Stored as text because an unsigned 64-bit value
    # does not fit portably in a signed BIGINT.
    fingerprint: Mapped[str] = mapped_column(String(16), default="0", index=True)

    seniority: Mapped[str | None] = mapped_column(String(32))
    min_years: Mapped[int | None] = mapped_column(Integer)
    max_years: Mapped[int | None] = mapped_column(Integer)
    education_level: Mapped[str | None] = mapped_column(String(48))
    education_fields: Mapped[list[str]] = mapped_column(JSON, default=list)

    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    salary_period: Mapped[str | None] = mapped_column(String(16))

    url: Mapped[str | None] = mapped_column(String(1024))
    posted_at: Mapped[date | None] = mapped_column(Date, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"))

    source: Mapped[JobSource] = relationship(back_populates="jobs")
    company: Mapped[Company | None] = relationship(back_populates="jobs")
    role: Mapped[Role | None] = relationship(back_populates="jobs")
    skill_links: Mapped[list[JobSkill]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class JobSkill(Base):
    """A requirement extracted from one posting."""

    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)

    # required | preferred | mentioned
    requirement_type: Mapped[str] = mapped_column(String(16), default="required")
    mention_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence: Mapped[str | None] = mapped_column(Text)

    job: Mapped[Job] = relationship(back_populates="skill_links")
    skill: Mapped[Skill] = relationship(back_populates="job_links")


class RoleSkillStatistic(Base):
    """Aggregated frequency of one skill within one role's posting set."""

    __tablename__ = "role_skill_statistics"
    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", name="uq_role_skill_stat"),
        Index("ix_stats_role_freq", "role_id", "frequency_pct"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)

    total_jobs: Mapped[int] = mapped_column(Integer)
    jobs_mentioning: Mapped[int] = mapped_column(Integer)
    frequency_pct: Mapped[float] = mapped_column(Float)
    required_pct: Mapped[float] = mapped_column(Float, default=0.0)
    preferred_pct: Mapped[float] = mapped_column(Float, default=0.0)
    # high | medium | low
    confidence: Mapped[str] = mapped_column(String(16), default="medium")
    rank: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[date | None] = mapped_column(Date)
    window_end: Mapped[date | None] = mapped_column(Date)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    role: Mapped[Role] = relationship(back_populates="statistics")
    skill: Mapped[Skill] = relationship()


class SkillTrend(Base):
    """Month-by-month frequency of a skill within a role."""

    __tablename__ = "skill_trends"
    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", "period", name="uq_skill_trend"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)

    period: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    total_jobs: Mapped[int] = mapped_column(Integer)
    jobs_mentioning: Mapped[int] = mapped_column(Integer)
    frequency_pct: Mapped[float] = mapped_column(Float)

    role: Mapped[Role] = relationship()
    skill: Mapped[Skill] = relationship()


class User(Base):
    """An anonymous skill profile.

    Deliberately holds no personal data: no email, no name, no login. The
    client generates an opaque token and keeps it in local storage. Deleting
    the row removes everything we ever held about that person.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    target_role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    skills: Mapped[list[UserSkill]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    target_role: Mapped[Role | None] = relationship()


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    # learning | working | strong
    proficiency: Mapped[str] = mapped_column(String(16), default="working")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped[User] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship()
