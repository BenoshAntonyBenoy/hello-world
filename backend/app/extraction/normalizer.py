"""Turn raw job-posting text into something analysable.

Handles the unglamorous half of extraction: cleaning HTML-ish noise, splitting
a posting into its real sections so "must have" can be told apart from "nice
to have", and pulling out the structured fields (years of experience, degree,
salary) that are not skills but still requirements.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

# --- Cleaning -----------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_RE = re.compile(r"&(nbsp|amp|lt|gt|quot|#39);")
_BULLET_RE = re.compile(r"^[\s]*[•▪◦●·*\-–—]+\s*", re.MULTILINE)
_WS_RE = re.compile(r"[ \t]+")
_BLANKS_RE = re.compile(r"\n{3,}")

_ENTITIES = {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "#39": "'"}


def normalize_text(raw: str) -> str:
    """Canonical plain-text form of a posting. Preserves line structure."""
    text = unicodedata.normalize("NFKC", raw or "")
    text = _TAG_RE.sub("\n", text)
    text = _ENTITY_RE.sub(lambda m: _ENTITIES.get(m.group(1), " "), text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BULLET_RE.sub("", text)
    text = _WS_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _BLANKS_RE.sub("\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    """Stable hash of the meaningful content, used for exact-duplicate checks."""
    collapsed = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return hashlib.sha256(collapsed.encode("utf-8")).hexdigest()


# --- Section detection ---------------------------------------------------------
#
# Postings vary wildly in structure, but the headings cluster into four intents.
# Getting this right is what lets us report "required" vs "preferred" honestly
# instead of flattening every mention into one bucket.

SECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "preferred",
        re.compile(
            r"^\s*(?:preferred|nice[\s-]to[\s-]have|good[\s-]to[\s-]have|bonus|"
            r"desirable|added\s+advantage|plus(?:es)?|it'?s\s+a\s+plus|"
            r"preferred\s+qualifications?|preferred\s+skills?|"
            r"what\s+would\s+set\s+you\s+apart)\b[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        "required",
        re.compile(
            r"^\s*(?:requirements?|required\s+skills?|must[\s-]have(?:s)?|"
            r"qualifications?|minimum\s+qualifications?|basic\s+qualifications?|"
            r"eligibility|key\s+skills?|skills?\s+(?:required|needed)|"
            r"what\s+(?:you'?ll\s+need|we'?re\s+looking\s+for|you\s+need)|"
            r"who\s+you\s+are|technical\s+skills?)\b[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        "responsibilities",
        re.compile(
            r"^\s*(?:responsibilities|key\s+responsibilities|what\s+you'?ll\s+do|"
            r"the\s+role|role\s+overview|job\s+description|about\s+the\s+role|"
            r"your\s+day[\s-]to[\s-]day|duties)\b[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        "boilerplate",
        re.compile(
            r"^\s*(?:benefits?|perks?|what\s+we\s+offer|compensation|about\s+us|"
            r"about\s+the\s+company|why\s+join|our\s+culture|equal\s+opportunity|"
            r"how\s+to\s+apply|diversity)\b[:\s]*$",
            re.IGNORECASE,
        ),
    ),
)

# Weight applied to a match depending on where it was found. Boilerplate is
# down-weighted heavily: "we're an AWS shop" in an About Us blurb is not a
# requirement of the job.
SECTION_CONFIDENCE = {
    "required": 1.0,
    "responsibilities": 0.85,
    "preferred": 0.9,
    "boilerplate": 0.35,
    "unknown": 0.7,
}


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split a posting into ``(section_kind, body)`` pairs.

    A line is treated as a heading only if it is short and matches a known
    heading pattern, which avoids mistaking a sentence containing the word
    "requirements" for a section break.
    """
    lines = text.split("\n")
    sections: list[tuple[str, list[str]]] = [("unknown", [])]

    for line in lines:
        stripped = line.strip().rstrip(":").strip()
        matched: str | None = None
        if 0 < len(stripped) <= 60:
            for kind, pattern in SECTION_PATTERNS:
                if pattern.match(stripped) or pattern.match(stripped + ":"):
                    matched = kind
                    break
        if matched:
            sections.append((matched, []))
        else:
            sections[-1][1].append(line)

    return [(kind, "\n".join(body).strip()) for kind, body in sections if "".join(body).strip()]


# --- Structured field extraction -------------------------------------------------

_YEARS_RANGE = re.compile(
    r"(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE
)
_YEARS_MIN = re.compile(
    r"(?:minimum\s+(?:of\s+)?|at\s+least\s+|min\.?\s*)?(\d{1,2})\s*\+\s*(?:years?|yrs?)",
    re.IGNORECASE,
)
_YEARS_SINGLE = re.compile(
    r"(?:minimum\s+(?:of\s+)?|at\s+least\s+)?(\d{1,2})\s*(?:years?|yrs?)\s+"
    r"(?:of\s+)?(?:relevant\s+|professional\s+|hands[\s-]on\s+|industry\s+)?experience",
    re.IGNORECASE,
)
_FRESHER = re.compile(
    r"\b(?:fresher|freshers|fresh\s+graduate|entry[\s-]level|no\s+prior\s+experience|"
    r"0\s*(?:-|–|to)\s*1\s*years?)\b",
    re.IGNORECASE,
)


def extract_experience(text: str) -> tuple[int | None, int | None]:
    """Best-effort ``(min_years, max_years)``.

    Ranges win over open-ended minimums, which win over bare mentions. Returns
    ``(None, None)`` when the posting genuinely does not say.
    """
    if m := _YEARS_RANGE.search(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        return (min(lo, hi), max(lo, hi))
    if m := _YEARS_MIN.search(text):
        return (int(m.group(1)), None)
    if m := _YEARS_SINGLE.search(text):
        return (int(m.group(1)), None)
    if _FRESHER.search(text):
        return (0, 1)
    return (None, None)


def experience_bucket(min_years: int | None, max_years: int | None) -> str:
    """Collapse a year range into the buckets the dashboard charts."""
    if min_years is None and max_years is None:
        return "Not specified"
    lo = min_years if min_years is not None else 0
    if lo <= 0:
        return "0–2 years"
    if lo < 2:
        return "0–2 years"
    if lo < 5:
        return "2–5 years"
    return "5+ years"


_DEGREE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("PhD", re.compile(r"\b(?:ph\.?\s?d|doctorate|doctoral)\b", re.IGNORECASE)),
    ("Master's", re.compile(
        r"\b(?:m\.?\s?tech|m\.?\s?e\b|m\.?\s?sc|mca|mba|master'?s?\s+degree|masters?)\b",
        re.IGNORECASE)),
    ("Bachelor's", re.compile(
        r"\b(?:b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|b\.?\s?com|bachelor'?s?\s+degree|"
        r"bachelors?|undergraduate\s+degree)\b",
        re.IGNORECASE)),
    ("Diploma", re.compile(r"\bdiploma\b", re.IGNORECASE)),
)

_FIELD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Computer Science", re.compile(r"\b(?:computer\s+science|cse?\b|comp\.?\s?sci)", re.IGNORECASE)),
    ("Information Technology", re.compile(r"\b(?:information\s+technology|\bit\s+engineering)\b", re.IGNORECASE)),
    ("Electronics", re.compile(r"\b(?:electronics|ece\b|e&tc)\b", re.IGNORECASE)),
    ("Electrical", re.compile(r"\b(?:electrical\s+engineering|eee\b)\b", re.IGNORECASE)),
    ("Mathematics", re.compile(r"\b(?:mathematics|maths?\b)\b", re.IGNORECASE)),
    ("Statistics", re.compile(r"\bstatistics\b", re.IGNORECASE)),
    ("Design", re.compile(r"\b(?:design|hci|human[\s-]computer\s+interaction)\b", re.IGNORECASE)),
    ("Business", re.compile(r"\b(?:business\s+administration|commerce|management)\b", re.IGNORECASE)),
    ("Marketing", re.compile(r"\bmarketing\b", re.IGNORECASE)),
)


_EDUCATION_LINE = re.compile(
    r"\b(?:ph\.?\s?d|doctorate|m\.?\s?tech|m\.?\s?e\b|m\.?\s?sc|mca|mba|masters?|"
    r"b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|b\.?\s?com|bachelors?|diploma|"
    r"degree|graduation|post[\s-]graduate)\b",
    re.IGNORECASE,
)


def strip_education_lines(text: str) -> str:
    """Remove degree-requirement lines before skill matching.

    "Bachelor's degree in Statistics" states a *field of study*, not that the
    employer wants statistical analysis as a working skill. Counting it as a
    skill mention inflates every subject that doubles as a discipline name —
    Statistics, Mathematics, Design, Marketing — by however often it appears
    in an education requirement.

    The degree itself is still captured: ``extract_education`` runs against the
    full untouched text.
    """
    kept = [
        line for line in text.split("\n")
        if not (_EDUCATION_LINE.search(line) and len(line) < 160)
    ]
    return "\n".join(kept)


def extract_education(text: str) -> tuple[str | None, list[str]]:
    """Highest degree mentioned plus the fields of study named alongside it."""
    level: str | None = None
    for name, pattern in _DEGREE_PATTERNS:
        if pattern.search(text):
            level = name
            break

    fields: list[str] = []
    if level:
        for name, pattern in _FIELD_PATTERNS:
            if pattern.search(text) and name not in fields:
                fields.append(name)
    return level, fields


_SALARY_RE = re.compile(
    r"(?:₹|rs\.?|inr)\s*(\d{1,3}(?:[,\d]{0,9}))\s*(?:-|–|to)\s*"
    r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:[,\d]{0,9}))\s*(lpa|per\s+annum|pa\b|lakh)?",
    re.IGNORECASE,
)


def extract_salary(text: str) -> tuple[int | None, int | None, str | None, str | None]:
    """Parse an explicitly stated salary range. Never infers one."""
    m = _SALARY_RE.search(text)
    if not m:
        return (None, None, None, None)
    try:
        lo = int(m.group(1).replace(",", ""))
        hi = int(m.group(2).replace(",", ""))
    except ValueError:
        return (None, None, None, None)
    unit = (m.group(3) or "").lower()
    if "lpa" in unit or "lakh" in unit:
        lo, hi = lo * 100_000, hi * 100_000
    if lo > hi:
        lo, hi = hi, lo
    return (lo, hi, "INR", "year")
