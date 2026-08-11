"""The requirement extraction pipeline.

    raw posting text
        -> normalize
        -> split into sections
        -> match taxonomy per section
        -> resolve requirement type (required / preferred / mentioned)
        -> pull structured fields (experience, education, salary)
        -> ExtractionResult

Deterministic and offline by default. ``app/extraction/llm.py`` describes the
optional LLM pass for phrases the taxonomy does not cover; it is disabled unless
an API key is configured, so results stay reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.extraction import normalizer
from app.extraction.dedupe import simhash
from app.extraction.matcher import get_matcher
from app.extraction.taxonomy import CATEGORY_LABELS, SkillDef

# Which section a match came from decides how we label it.
_TYPE_BY_SECTION = {
    "required": "required",
    "responsibilities": "required",
    "preferred": "preferred",
    "boilerplate": "mentioned",
    "unknown": "required",
}

_EVIDENCE_RADIUS = 70


@dataclass
class ExtractedSkill:
    skill: SkillDef
    requirement_type: str
    mention_count: int
    confidence: float
    evidence: str

    @property
    def canonical(self) -> str:
        return self.skill.canonical

    @property
    def category(self) -> str:
        return self.skill.category

    @property
    def display_category(self) -> str:
        return CATEGORY_LABELS.get(self.skill.category, "Other Requirements")


@dataclass
class ExtractionResult:
    normalized_text: str
    content_hash: str
    fingerprint: int
    skills: list[ExtractedSkill] = field(default_factory=list)
    min_years: int | None = None
    max_years: int | None = None
    experience_bucket: str = "Not specified"
    education_level: str | None = None
    education_fields: list[str] = field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    salary_period: str | None = None

    def canonical_names(self) -> set[str]:
        return {s.canonical for s in self.skills}

    def by_display_category(self) -> dict[str, list[ExtractedSkill]]:
        grouped: dict[str, list[ExtractedSkill]] = {}
        for s in self.skills:
            grouped.setdefault(s.display_category, []).append(s)
        for items in grouped.values():
            items.sort(key=lambda s: (-s.confidence, s.canonical))
        return grouped


def _evidence_snippet(text: str, start: int, end: int) -> str:
    lo = max(0, start - _EVIDENCE_RADIUS)
    hi = min(len(text), end + _EVIDENCE_RADIUS)
    snippet = text[lo:hi].replace("\n", " ").strip()
    if lo > 0:
        snippet = "…" + snippet
    if hi < len(text):
        snippet = snippet + "…"
    return snippet


def extract(raw_text: str) -> ExtractionResult:
    """Run the full pipeline over one posting."""
    text = normalizer.normalize_text(raw_text)
    result = ExtractionResult(
        normalized_text=text,
        content_hash=normalizer.content_hash(text),
        fingerprint=simhash(text),
    )

    matcher = get_matcher()
    # canonical -> aggregated state across every section of this posting
    best: dict[str, ExtractedSkill] = {}

    for section_kind, raw_body in normalizer.split_sections(text):
        section_conf = normalizer.SECTION_CONFIDENCE.get(section_kind, 0.7)
        req_type = _TYPE_BY_SECTION.get(section_kind, "required")
        # Degree lines name fields of study, not working skills.
        body = normalizer.strip_education_lines(raw_body)
        if not body.strip():
            continue

        for match in matcher.find(body):
            canonical = match.skill.canonical
            confidence = section_conf
            # A skill named in a bare list gets slightly less weight than one
            # written into a sentence, which usually carries real intent.
            if len(body.split()) < 8:
                confidence *= 0.9

            existing = best.get(canonical)
            if existing is None:
                best[canonical] = ExtractedSkill(
                    skill=match.skill,
                    requirement_type=req_type,
                    mention_count=1,
                    confidence=round(confidence, 3),
                    evidence=_evidence_snippet(body, match.start, match.end),
                )
                continue

            existing.mention_count += 1
            # "required" anywhere beats "preferred" anywhere; both beat "mentioned".
            if _rank(req_type) > _rank(existing.requirement_type):
                existing.requirement_type = req_type
                existing.evidence = _evidence_snippet(body, match.start, match.end)
            existing.confidence = round(max(existing.confidence, confidence), 3)

    # Repeated mentions are weak corroboration, capped so a keyword-stuffed
    # posting cannot manufacture certainty.
    for item in best.values():
        bonus = min(0.15, 0.05 * (item.mention_count - 1))
        item.confidence = round(min(1.0, item.confidence + bonus), 3)

    result.skills = sorted(best.values(), key=lambda s: (-s.confidence, s.canonical))

    result.min_years, result.max_years = normalizer.extract_experience(text)
    result.experience_bucket = normalizer.experience_bucket(
        result.min_years, result.max_years
    )
    result.education_level, result.education_fields = normalizer.extract_education(text)
    (
        result.salary_min,
        result.salary_max,
        result.salary_currency,
        result.salary_period,
    ) = normalizer.extract_salary(text)

    return result


def _rank(requirement_type: str) -> int:
    return {"mentioned": 0, "preferred": 1, "required": 2}.get(requirement_type, 0)
