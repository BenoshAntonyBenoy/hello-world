"""Optional LLM-assisted extraction for phrases the taxonomy misses.

Why this is opt-in rather than the default path:

* **Reproducibility.** Frequency statistics are the product. If the same corpus
  yields different numbers on different runs, the numbers stop meaning anything.
* **Cost.** One call per posting across tens of thousands of postings is real
  money for a marginal recall gain over a well-maintained taxonomy.
* **Auditability.** A regex match points at the exact span it matched. A model
  output does not, unless you ask for it and verify it.

So the rule-based pipeline handles everything it recognises, and the model is
used only for the residue: requirement-shaped sentences containing no known
skill. Anything it proposes is a *candidate* for the taxonomy — surfaced for
review, never silently counted in published statistics.

Enable by setting ``LLM_EXTRACTION_ENABLED=true`` and ``ANTHROPIC_API_KEY``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.extraction.matcher import get_matcher

_REQUIREMENT_HINT = re.compile(
    r"\b(?:experience|proficien|knowledge|familiar|expertise|skills?|"
    r"understanding|hands[\s-]on|working\s+with|ability\s+to)\b",
    re.IGNORECASE,
)

EXTRACTION_PROMPT = """\
You are extracting hiring requirements from a job posting.

Return a JSON array. Each element must be:
  {"term": "<the requirement as a canonical noun phrase>",
   "category": "language|framework|tool|platform|concept|soft|certification|other",
   "evidence": "<the exact substring of the input that states it>"}

Rules:
- Only include requirements literally stated in the text.
- Do not infer, expand, or add anything the posting does not say.
- If the evidence substring is not present verbatim in the input, omit the item.
- Return [] if there are no requirements.

Job posting excerpt:
---
{excerpt}
---
"""


@dataclass(frozen=True)
class CandidateTerm:
    term: str
    category: str
    evidence: str


def is_enabled() -> bool:
    return bool(settings.llm_extraction_enabled and settings.anthropic_api_key)


def residual_sentences(text: str, limit: int = 12) -> list[str]:
    """Requirement-shaped sentences containing no taxonomy match.

    This is the only input the model ever sees, which keeps token spend
    proportional to the gap in our vocabulary rather than to corpus size.
    """
    matcher = get_matcher()
    out: list[str] = []
    for raw in re.split(r"(?<=[.;\n])\s+", text):
        sentence = raw.strip()
        if len(sentence) < 25 or not _REQUIREMENT_HINT.search(sentence):
            continue
        if matcher.find(sentence):
            continue
        out.append(sentence)
        if len(out) >= limit:
            break
    return out


def propose_terms(text: str) -> list[CandidateTerm]:
    """Ask the model for requirement terms the taxonomy does not cover.

    Returns ``[]`` when disabled, so callers need no branching. The network call
    is intentionally left unimplemented: wiring it up is a deployment decision,
    and the MVP must run fully offline.
    """
    if not is_enabled():
        return []

    residues = residual_sentences(text)
    if not residues:
        return []

    raise NotImplementedError(
        "LLM extraction is enabled but no client is wired up. Implement the "
        "call to the Anthropic Messages API here using EXTRACTION_PROMPT, "
        "validate that each returned `evidence` string appears verbatim in the "
        "input, and route accepted terms to taxonomy review rather than "
        "directly into published statistics."
    )
