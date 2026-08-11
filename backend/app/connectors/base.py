"""The Job Data Connector contract.

Every source of postings — a licensed API, a public feed, a CSV export, a job
description a user pasted in — arrives through this one interface. The rest of
the pipeline never learns where a posting came from, which is what makes adding
a source a self-contained change.

Compliance is part of the contract, not an afterthought. A connector must
declare its ``kind`` and, where relevant, its terms URL. Connectors that would
require scraping behind authentication, defeating anti-bot measures, or
ignoring robots.txt are not implemented here and must not be added: see
``docs/DATA_SOURCES.md`` for the accepted routes to each major board.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class SourceDescriptor:
    """Provenance and legal basis for one source."""

    key: str
    name: str
    # api | licensed_dataset | public_feed | user_submitted | synthetic
    kind: str
    base_url: str | None = None
    terms_url: str | None = None
    requires_license: bool = False
    notes: str = ""


@dataclass
class RawPosting:
    """One posting as it arrives, before normalization or extraction."""

    external_id: str
    title: str
    description: str
    company: str | None = None
    location: str | None = None
    country: str | None = "India"
    employment_type: str | None = None
    url: str | None = None
    posted_at: date | None = None
    # Optional hint from the source about which role this is; the pipeline
    # still validates it against the posting text.
    role_hint: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


class JobDataConnector(ABC):
    """Base class for all job data sources."""

    #: Stable identifier used in configuration and stored on every job row.
    key: str = ""

    @property
    @abstractmethod
    def descriptor(self) -> SourceDescriptor:
        """Provenance metadata, persisted to ``job_sources``."""

    @abstractmethod
    def fetch(
        self,
        role_slugs: Iterable[str] | None = None,
        limit: int | None = None,
    ) -> Iterator[RawPosting]:
        """Yield postings, optionally restricted to specific roles.

        Implementations should stream rather than materialise: a licensed feed
        may hold millions of rows.
        """

    def health_check(self) -> tuple[bool, str]:
        """Whether the source is reachable and correctly configured."""
        return True, "ok"

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} key={self.key!r}>"
