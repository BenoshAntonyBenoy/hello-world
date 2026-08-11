"""Connector for job descriptions a user pastes in themselves.

The one source that needs no licensing negotiation: a person supplying a
posting they are already looking at. It powers ``POST /api/analyze-job`` and
doubles as the escape hatch for roles or regions no feed covers yet.

Submissions are held in memory for the life of the process rather than written
to the shared corpus. Letting arbitrary pasted text move published market
statistics would be trivially abusable; promoting a submission into the corpus
should be a reviewed action, not a side effect of using the analyser.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import date, datetime, timezone

from app.connectors.base import JobDataConnector, RawPosting, SourceDescriptor
from app.connectors.registry import register


class UserSubmittedConnector(JobDataConnector):
    key = "user_submitted"

    def __init__(self, max_buffered: int = 500) -> None:
        self._buffer: list[RawPosting] = []
        self._max_buffered = max_buffered

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            key=self.key,
            name="User-submitted job description",
            kind="user_submitted",
            notes=(
                "Text supplied directly by a user for one-off analysis. Not "
                "merged into role statistics without review."
            ),
        )

    def submit(
        self,
        description: str,
        title: str = "Pasted job description",
        company: str | None = None,
        location: str | None = None,
        url: str | None = None,
        role_hint: str | None = None,
    ) -> RawPosting:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        posting = RawPosting(
            external_id=f"user-{stamp}",
            title=title.strip() or "Pasted job description",
            description=description,
            company=company,
            location=location,
            url=url,
            posted_at=date.today(),
            role_hint=role_hint,
        )
        self._buffer.append(posting)
        if len(self._buffer) > self._max_buffered:
            self._buffer.pop(0)
        return posting

    def fetch(
        self,
        role_slugs: Iterable[str] | None = None,
        limit: int | None = None,
    ) -> Iterator[RawPosting]:
        wanted = set(role_slugs) if role_slugs else None
        count = 0
        for posting in list(self._buffer):
            if wanted and posting.role_hint not in wanted:
                continue
            yield posting
            count += 1
            if limit and count >= limit:
                return


user_submitted = UserSubmittedConnector()
register(user_submitted)
