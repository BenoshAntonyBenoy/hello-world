"""Surface-form matching against the skill taxonomy.

This is deliberately not a bag-of-words keyword counter. Three things make the
difference between a usable statistic and a misleading one:

1. **Custom token boundaries.** ``C`` must not match inside ``C++``; ``Java``
   must not match inside ``JavaScript``; ``SQL`` must not match inside
   ``MySQL``. Plain ``\\b`` gets all three wrong.
2. **Context gating for ambiguous tokens.** ``R``, ``Go`` and ``C`` are real
   languages and also extremely common English fragments. They only count when
   a supporting word appears nearby.
3. **Trap phrases.** ``R&D`` is not the R language; ``go-to-market`` is not Go.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.extraction.taxonomy import CATALOG, SkillDef

# Characters that may not sit directly against an alphanumeric surface form.
_LEFT_GUARD = r"(?<![A-Za-z0-9_+#])"
_RIGHT_GUARD = r"(?![A-Za-z0-9_+#])"

# How far either side of an ambiguous token we look for a supporting word.
_CONTEXT_WINDOW = 90

# Known false friends. Checked against the text immediately around a match,
# for every skill — not only the ambiguous short ones. "Reporting to the
# leadership team" describes the org chart, not a required competency, and it
# appears in a large share of real postings.
_TRAPS: dict[str, tuple[re.Pattern[str], ...]] = {
    "R": (
        re.compile(r"R\s*&\s*D", re.IGNORECASE),
        re.compile(r"\bR\s*/\s*D\b", re.IGNORECASE),
    ),
    "Go": (
        re.compile(r"go[\s-]to[\s-]market", re.IGNORECASE),
        re.compile(r"\bgo\s+live\b", re.IGNORECASE),
        re.compile(r"\bgo[\s-]getter\b", re.IGNORECASE),
    ),
    "C": (
        re.compile(r"\bc[\s-]level\b", re.IGNORECASE),
        re.compile(r"\bvitamin\s+c\b", re.IGNORECASE),
    ),
    "Leadership": (
        re.compile(r"\b(?:senior\s+|the\s+|our\s+|executive\s+)?leadership\s+"
                   r"(?:team|group|meeting|review|forum)\b", re.IGNORECASE),
        re.compile(r"\breport(?:s|ing)?\s+to\s+(?:the\s+)?leadership\b", re.IGNORECASE),
    ),
    "Agile": (
        # "agile environment" is a description of the workplace, not a skill
        # request, but it is close enough that we keep it; genuinely unrelated
        # uses of the adjective are what this catches.
        re.compile(r"\bagile\s+(?:mindset\s+)?about\b", re.IGNORECASE),
    ),
}

# How far around a match we look for a trap phrase.
_TRAP_WINDOW = 40


def _form_pattern(form: str) -> str:
    """Regex for one surface form, with boundaries that respect ``+``/``#``/``.``."""
    escaped = re.escape(form)
    # Allow a space, hyphen or dot wherever the canonical form has one, so
    # "Next.js" also matches "next js" and "scikit-learn" matches "scikit learn".
    escaped = escaped.replace(r"\ ", r"[\s\-\.]?").replace(r"\-", r"[\s\-]?")
    escaped = escaped.replace(r"\.", r"[\.\s\-]?")

    left = _LEFT_GUARD if form[0].isalnum() else r"(?<![A-Za-z0-9_])"
    right = _RIGHT_GUARD if form[-1].isalnum() else r"(?![A-Za-z0-9_])"
    return f"{left}{escaped}{right}"


@dataclass(frozen=True)
class Match:
    skill: SkillDef
    start: int
    end: int
    surface: str


class SkillMatcher:
    """Compiled matcher over the whole taxonomy.

    Build once and reuse — compiling ~180 alternation patterns is the expensive
    part, and it is entirely reusable across postings.
    """

    def __init__(self, catalog: tuple[SkillDef, ...] = CATALOG) -> None:
        self._catalog = catalog
        self._patterns: list[tuple[SkillDef, re.Pattern[str]]] = []

        for skill in catalog:
            # Longest form first so "React Native" wins over "React".
            forms = sorted(skill.surface_forms, key=len, reverse=True)
            alternation = "|".join(_form_pattern(f) for f in forms)
            # Ambiguous single letters must match case-sensitively: the language
            # is "R", not the letter "r" in the middle of a sentence.
            flags = 0 if (skill.strict and len(skill.canonical) <= 2) else re.IGNORECASE
            self._patterns.append((skill, re.compile(alternation, flags)))

    def find(self, text: str) -> list[Match]:
        """All taxonomy matches in ``text``, ambiguity already filtered out."""
        lowered = text.lower()
        results: list[Match] = []

        for skill, pattern in self._patterns:
            for m in pattern.finditer(text):
                if self._is_trap(skill, text, m):
                    continue
                if skill.strict and not self._has_context(skill, lowered, m):
                    continue
                results.append(Match(skill, m.start(), m.end(), m.group(0)))

        return self._resolve_overlaps(results)

    @staticmethod
    def _is_trap(skill: SkillDef, text: str, m: re.Match[str]) -> bool:
        traps = _TRAPS.get(skill.canonical)
        if not traps:
            return False
        lo = max(0, m.start() - _TRAP_WINDOW)
        hi = min(len(text), m.end() + _TRAP_WINDOW)
        window = text[lo:hi]
        return any(trap.search(window) for trap in traps)

    @staticmethod
    def _has_context(skill: SkillDef, lowered: str, m: re.Match[str]) -> bool:
        if not skill.context_words:
            return True
        lo = max(0, m.start() - _CONTEXT_WINDOW)
        hi = min(len(lowered), m.end() + _CONTEXT_WINDOW)
        window = lowered[lo:hi]
        return any(word in window for word in skill.context_words)

    @staticmethod
    def _resolve_overlaps(matches: list[Match]) -> list[Match]:
        """Longest match wins where two different skills cover the same text.

        "Communication Protocols" contains "Communication"; without this, a
        firmware posting that never mentions communication *skills* still adds
        one to that tally. Same for "Data Structures & Algorithms" and any
        future taxonomy entry that nests inside another.
        """
        if len(matches) < 2:
            return matches

        # Longest span first, so the winner is always seen before its victims.
        ordered = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
        kept: list[Match] = []

        for candidate in ordered:
            covered = any(
                other.skill.canonical != candidate.skill.canonical
                and other.start <= candidate.start
                and other.end >= candidate.end
                and (other.end - other.start) > (candidate.end - candidate.start)
                for other in ordered
            )
            if not covered:
                kept.append(candidate)

        return kept


_matcher: SkillMatcher | None = None


def get_matcher() -> SkillMatcher:
    """Process-wide singleton — the compiled patterns are immutable."""
    global _matcher
    if _matcher is None:
        _matcher = SkillMatcher()
    return _matcher
