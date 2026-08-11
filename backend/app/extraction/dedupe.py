"""Duplicate detection and relevance filtering.

Job boards are full of the same posting reposted weekly, cross-listed by
staffing agencies, or duplicated across sources. Counting those repeats inflates
whatever skills that one company happens to want. Both checks here run *before*
statistics are computed.
"""

from __future__ import annotations

import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")
_SHINGLE = 3
_HASH_BITS = 64
_MASK = (1 << _HASH_BITS) - 1

# Hamming distance below which two postings are considered the same listing.
NEAR_DUPLICATE_THRESHOLD = 6


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _hash_token(token: str) -> int:
    """FNV-1a, chosen for being stable across processes and Python versions.

    ``hash()`` is randomised per process, which would make simhashes computed in
    one run incomparable with the next.
    """
    h = 0xCBF29CE484222325
    for byte in token.encode("utf-8"):
        h ^= byte
        h = (h * 0x100000001B3) & _MASK
    return h


def simhash(text: str) -> int:
    """64-bit similarity fingerprint over token shingles."""
    tokens = tokenize(text)
    if not tokens:
        return 0

    shingles = (
        [" ".join(tokens[i : i + _SHINGLE]) for i in range(len(tokens) - _SHINGLE + 1)]
        if len(tokens) >= _SHINGLE
        else tokens
    )

    vector = [0] * _HASH_BITS
    for shingle, weight in Counter(shingles).items():
        h = _hash_token(shingle)
        for bit in range(_HASH_BITS):
            vector[bit] += weight if (h >> bit) & 1 else -weight

    out = 0
    for bit in range(_HASH_BITS):
        if vector[bit] > 0:
            out |= 1 << bit
    return out


def hamming(a: int, b: int) -> int:
    return ((a ^ b) & _MASK).bit_count()


def is_near_duplicate(a: int, b: int, threshold: int = NEAR_DUPLICATE_THRESHOLD) -> bool:
    return hamming(a, b) <= threshold


def to_hex(fingerprint: int) -> str:
    """Storage form — 16 hex chars, portable across SQLite and Postgres."""
    return format(fingerprint & _MASK, "016x")


def from_hex(value: str | None) -> int:
    try:
        return int(value, 16) if value else 0
    except (TypeError, ValueError):
        return 0


class DuplicateIndex:
    """Incremental near-duplicate index used during ingestion.

    Banded lookup keeps this roughly linear: a full pairwise comparison over
    tens of thousands of postings would not finish in reasonable time.
    """

    _BANDS = 4
    _BAND_BITS = _HASH_BITS // _BANDS

    def __init__(self) -> None:
        self._exact: dict[str, int] = {}
        self._bands: list[dict[int, list[tuple[int, int]]]] = [
            {} for _ in range(self._BANDS)
        ]

    def _band_keys(self, fingerprint: int) -> list[int]:
        return [
            (fingerprint >> (i * self._BAND_BITS)) & ((1 << self._BAND_BITS) - 1)
            for i in range(self._BANDS)
        ]

    def find_exact(self, content_hash: str) -> int | None:
        """Job id whose text is byte-for-byte equivalent, if any.

        Kept separate from near-duplicate lookup because the two deserve
        different handling: an exact repost carries no new information and is
        not stored at all, whereas a near-duplicate is a genuinely distinct
        document describing the same vacancy and is worth keeping for
        provenance.
        """
        return self._exact.get(content_hash)

    def find_near(self, fingerprint: int) -> int | None:
        """Job id with a similar-but-not-identical body, if any."""
        for band, key in enumerate(self._band_keys(fingerprint)):
            for other_fp, job_id in self._bands[band].get(key, ()):
                if is_near_duplicate(fingerprint, other_fp):
                    return job_id
        return None

    def find_duplicate(self, content_hash: str, fingerprint: int) -> int | None:
        """Either kind of duplicate, exact checked first."""
        if (existing := self.find_exact(content_hash)) is not None:
            return existing
        return self.find_near(fingerprint)

    def add(self, content_hash: str, fingerprint: int, job_id: int) -> None:
        self._exact.setdefault(content_hash, job_id)
        for band, key in enumerate(self._band_keys(fingerprint)):
            self._bands[band].setdefault(key, []).append((fingerprint, job_id))


# --- Relevance ------------------------------------------------------------------

_JUNK_MARKERS = (
    "work from home typing",
    "no experience needed earn",
    "registration fee",
    "pay to apply",
    "data entry unlimited earning",
)


def relevance_score(
    title: str,
    text: str,
    role_title: str,
    role_aliases: tuple[str, ...],
    core_skills_found: int,
) -> float:
    """How confidently this posting belongs to the searched role, 0.0–1.0.

    Combines title agreement with whether the posting actually contains the
    role's core skills. A "Data Analyst" listing that mentions none of SQL,
    Excel or reporting is almost certainly mis-titled or spam.
    """
    title_l = title.lower()
    text_l = text.lower()

    if any(marker in text_l for marker in _JUNK_MARKERS):
        return 0.0
    if len(tokenize(text)) < 40:
        return 0.2

    score = 0.0
    wanted = [role_title.lower(), *(a.lower() for a in role_aliases)]
    if any(w in title_l for w in wanted):
        score += 0.6
    elif any(w in text_l for w in wanted):
        score += 0.3
    else:
        # Partial title overlap: "Senior ML Engineer" vs "Machine Learning Engineer"
        role_tokens = set(tokenize(role_title))
        overlap = role_tokens & set(tokenize(title))
        if role_tokens:
            score += 0.4 * (len(overlap) / len(role_tokens))

    score += min(0.4, core_skills_found * 0.1)
    return round(min(1.0, score), 3)


RELEVANCE_THRESHOLD = 0.45
