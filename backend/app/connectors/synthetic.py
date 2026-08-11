"""Synthetic corpus connector — the development / demo data source.

This exists so the product is fully explorable before a licensed feed is
connected. Three properties keep it honest:

* **Companies are fictional.** Inventing a listing and attributing it to a real
  employer would be fabricating a record about that company. Names here are
  generated from neutral word pools and every posting is stamped
  ``kind="synthetic"`` so the UI can label it.
* **Nothing is pre-computed.** The generator writes *prose*. Every statistic the
  dashboard shows is recovered by the real extractor reading that prose, so the
  pipeline is genuinely exercised rather than bypassed.
* **It is deterministic.** Same ``SEED_RANDOM_STATE`` gives the same corpus on
  every machine, so numbers are reproducible.

The generator deliberately emits messy input: aliases instead of canonical
names ("ReactJS", "Amazon Web Services", "k8s"), a slice of duplicate reposts,
and a few off-topic listings — so dedup, synonym resolution and relevance
filtering all have something to do.
"""

from __future__ import annotations

import calendar
import random
from collections.abc import Iterable, Iterator
from datetime import date, timedelta

from app.config import settings
from app.connectors.base import JobDataConnector, RawPosting, SourceDescriptor
from app.connectors.registry import register
from app.data.roles import ROLE_PROFILES, RoleProfile
from app.extraction.taxonomy import BY_CANONICAL

# --- Word pools ----------------------------------------------------------------

_COMPANY_PREFIX = (
    "Northwind", "Bluepeak", "Meridian", "Lumenworks", "Trailhead", "Cobalt",
    "Vantage", "Quillon", "Silverline", "Brightfold", "Nimbus Grove", "Terrafirm",
    "Kaveri", "Ashvin", "Indus Loom", "Copperline", "Halcyon", "Redstone Bay",
    "Aeronaut", "Fernwood", "Sable Reef", "Tessellate", "Ironvale", "Marigold",
)
_COMPANY_SUFFIX = (
    "Technologies", "Systems", "Labs", "Analytics", "Digital", "Software",
    "Networks", "Solutions", "Works", "Studio", "Sciences", "Platforms",
)
_LOCATIONS = (
    "Bengaluru", "Hyderabad", "Pune", "Chennai", "Gurugram", "Noida", "Mumbai",
    "Kochi", "Ahmedabad", "Coimbatore", "Thiruvananthapuram", "Remote (India)",
    "Indore", "Jaipur", "Kolkata",
)
_TEAMS = (
    "platform", "core product", "growth", "data", "infrastructure",
    "customer experience", "innovation", "engineering",
)
_EMPLOYMENT = ("Full-time", "Full-time", "Full-time", "Contract", "Internship")

_TITLE_PREFIX = {
    "0-2": ("", "", "Junior ", "Associate ", "Graduate "),
    "2-5": ("", "", "", "Mid-level "),
    "5+": ("Senior ", "Senior ", "Lead ", "Staff "),
}

_REQUIRED_TEMPLATES = (
    "Strong proficiency in {s}",
    "Hands-on experience with {s}",
    "Solid understanding of {s}",
    "Working knowledge of {s}",
    "Demonstrated experience building with {s}",
    "Practical experience in {s}",
    "{s}",
    "{s} — day-to-day usage expected",
    "Comfortable working with {s} in a production setting",
)
_PREFERRED_TEMPLATES = (
    "Exposure to {s} is a plus",
    "Familiarity with {s}",
    "{s} experience preferred",
    "Bonus points for {s}",
    "Nice to have: {s}",
    "Any experience with {s} will be an added advantage",
)
_RESPONSIBILITY_TEMPLATES = (
    "Design, build and maintain solutions using {s}",
    "Partner with the team to deliver features that rely on {s}",
    "Own and improve our {s} workflows end to end",
    "Contribute to code reviews and technical discussions involving {s}",
    "Translate requirements into working solutions with {s}",
)
_INTRO_TEMPLATES = (
    "{company} is hiring a {title} to join our {team} team in {location}.",
    "We are looking for a {title} to strengthen the {team} team at {company}, based in {location}.",
    "{company} is expanding its {team} team and is looking for a {title} in {location}.",
    "Join {company} as a {title}. This role sits within our {team} team in {location}.",
    # A slice of postings that never restate the title in the body, as real
    # ones often don't — otherwise any role whose name contains a taxonomy term
    # is pinned to exactly 100% by its own headline.
    "{company} is growing the {team} team in {location} and has an opening.",
    "We have an opening on the {team} team at {company} in {location}.",
)
# Deliberately free of taxonomy terms. An identical skill-bearing sentence in
# every posting would pin whatever it mentions to 100% and look like a finding.
_ABOUT_LINES = (
    "You will work closely with a small, senior team and own your area end to end.",
    "This is a hands-on role with a clear path to greater scope over time.",
    "We care about craft, and we ship carefully rather than quickly.",
    "The team is distributed across two offices and meets in person each quarter.",
    "You will join early enough to shape how the team works, not just what it builds.",
    "Expect a high degree of autonomy and a low tolerance for unnecessary process.",
)

_BOILERPLATE = (
    "Competitive compensation, health insurance for you and your dependents, "
    "and an annual learning budget.",
    "Flexible working hours, a hybrid schedule, and a yearly wellness stipend.",
    "We are an equal opportunity employer and welcome applicants from all backgrounds.",
    "Quarterly team offsites, generous leave policy, and a supportive engineering culture.",
)

_EXPERIENCE_PHRASES = {
    "0-2": (
        "0-2 years of experience, freshers with strong fundamentals are welcome",
        "0 to 2 years of relevant experience",
        "Entry-level role; internship experience is valued",
    ),
    "2-5": (
        "2-5 years of professional experience",
        "Minimum of 2 years of hands-on experience",
        "3+ years of relevant experience",
    ),
    "5+": (
        "5+ years of industry experience",
        "At least 6 years of professional experience",
        "5-9 years of experience in a similar role",
    ),
}

_OFF_TOPIC = (
    ("Field Sales Executive", "Meet monthly targets across assigned territory. "
     "Two-wheeler required. Incentives on every closed deal. Excellent "
     "communication is essential for this customer-facing sales position."),
    ("Warehouse Supervisor", "Oversee daily inbound and outbound shipments, "
     "manage a team of loaders, maintain stock registers and coordinate with "
     "transport partners. Prior warehouse floor experience preferred."),
    ("Front Desk Executive", "Greet visitors, manage the appointment calendar, "
     "handle incoming calls and courier dispatch. Pleasant personality and "
     "fluency in English and the local language required."),
)


class SyntheticCorpusConnector(JobDataConnector):
    """Generates a reproducible, clearly-labelled sample corpus."""

    key = "mock_dataset"

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            key=self.key,
            name="Synthetic sample corpus",
            kind="synthetic",
            notes=(
                "Generated locally for development and demos. Companies are "
                "fictional; postings do not describe real vacancies. Replace "
                "with a licensed feed or official API before publishing any "
                "statistic as market fact."
            ),
        )

    # -- generation ---------------------------------------------------------

    def fetch(
        self,
        role_slugs: Iterable[str] | None = None,
        limit: int | None = None,
    ) -> Iterator[RawPosting]:
        wanted = set(role_slugs) if role_slugs else None
        rng = random.Random(settings.seed_random_state)
        months = max(1, settings.seed_history_months)
        per_role = max(months, settings.seed_postings_per_role)
        today = date.today()

        emitted = 0
        for profile in ROLE_PROFILES:
            if wanted and profile.slug not in wanted:
                continue

            per_month = max(1, per_role // months)
            recent_pool: list[RawPosting] = []

            for month_index in range(months):
                # month_index 0 is the oldest month in the window.
                age_months = months - 1 - month_index
                for n in range(per_month):
                    posted = self._date_in_month(rng, today, age_months)
                    posting = self._make_posting(
                        rng, profile, month_index, months, posted, n
                    )
                    recent_pool.append(posting)
                    yield posting
                    emitted += 1
                    if limit and emitted >= limit:
                        return

                    # ~3% of a real feed is the same listing reposted.
                    if rng.random() < 0.03 and recent_pool:
                        dup = rng.choice(recent_pool[-25:])
                        yield self._repost(rng, dup, posted)
                        emitted += 1
                        if limit and emitted >= limit:
                            return

            # A couple of genuinely off-topic listings that a title-based
            # search would wrongly pull in, so the relevance filter has work.
            for title, body in rng.sample(_OFF_TOPIC, k=2):
                yield RawPosting(
                    external_id=f"syn-{profile.slug}-noise-{title[:6].lower()}",
                    title=title,
                    description=body,
                    company=self._company(rng),
                    location=rng.choice(_LOCATIONS),
                    employment_type="Full-time",
                    posted_at=today - timedelta(days=rng.randint(1, 60)),
                    role_hint=profile.slug,
                )
                emitted += 1
                if limit and emitted >= limit:
                    return

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _date_in_month(rng: random.Random, today: date, age_months: int) -> date:
        """A date inside a specific *calendar* month.

        Stepping back in 30-day increments would straddle month boundaries and
        leave the YYYY-MM buckets uneven, which shows up downstream as trend
        noise in skills whose demand is actually flat.
        """
        year, month = today.year, today.month - age_months
        while month <= 0:
            month += 12
            year -= 1
        last_day = calendar.monthrange(year, month)[1]
        if (year, month) == (today.year, today.month):
            last_day = min(last_day, today.day)
        return date(year, month, rng.randint(1, max(1, last_day)))

    @staticmethod
    def _company(rng: random.Random) -> str:
        return f"{rng.choice(_COMPANY_PREFIX)} {rng.choice(_COMPANY_SUFFIX)}"

    @staticmethod
    def _surface(rng: random.Random, canonical: str) -> str:
        """Pick canonical or one of its aliases, so synonym handling is tested."""
        skill = BY_CANONICAL.get(canonical)
        if skill is None or not skill.aliases:
            return canonical
        # Aliases appear a minority of the time, as in real postings.
        if rng.random() < 0.32:
            return rng.choice(skill.aliases)
        return canonical

    def _probabilities(
        self, profile: RoleProfile, month_index: int, months: int
    ) -> dict[str, float]:
        """Skill probabilities for one month, with trends interpolated."""
        probs: dict[str, float] = {}
        probs.update(profile.core)
        probs.update(profile.common)
        probs.update(profile.optional)

        t = month_index / max(1, months - 1)
        for name, (start, end) in profile.emerging.items():
            probs[name] = start + (end - start) * t
        for name, (start, end) in profile.declining.items():
            probs[name] = start + (end - start) * t
        return probs

    def _make_posting(
        self,
        rng: random.Random,
        profile: RoleProfile,
        month_index: int,
        months: int,
        posted: date,
        n: int,
    ) -> RawPosting:
        probs = self._probabilities(profile, month_index, months)
        band = self._weighted_choice(rng, profile.experience_mix)
        company = self._company(rng)
        location = rng.choice(_LOCATIONS)
        title = f"{rng.choice(_TITLE_PREFIX[band])}{profile.title}"

        # Decide which skills this particular posting asks for.
        selected = [name for name, p in probs.items() if rng.random() < p]
        if not selected:
            selected = list(profile.core)[:3]
        rng.shuffle(selected)

        # Split into required vs preferred. Core skills almost never land in
        # the "nice to have" list.
        required: list[str] = []
        preferred: list[str] = []
        for name in selected:
            is_core = name in profile.core
            if not is_core and rng.random() < 0.3:
                preferred.append(name)
            else:
                required.append(name)

        responsibilities = required[: rng.randint(3, 5)]

        parts: list[str] = [
            rng.choice(_INTRO_TEMPLATES).format(
                company=company, title=title, team=rng.choice(_TEAMS), location=location
            ),
            "",
            "About the role",
            rng.choice(_ABOUT_LINES),
            "",
            "Responsibilities",
        ]
        for name in responsibilities:
            parts.append(
                rng.choice(_RESPONSIBILITY_TEMPLATES).format(
                    s=self._surface(rng, name)
                )
            )

        parts += ["", "Requirements"]
        for name in required[:12]:
            parts.append(
                rng.choice(_REQUIRED_TEMPLATES).format(s=self._surface(rng, name))
            )
        parts.append(rng.choice(_EXPERIENCE_PHRASES[band]))

        degree = self._weighted_choice(rng, profile.degree_mix)
        if degree:
            field = rng.choice(profile.education_fields)
            parts.append(
                rng.choice((
                    f"{degree} degree in {field} or a related discipline",
                    f"{degree} in {field}",
                    f"{degree} degree ({field}) or equivalent practical experience",
                ))
            )

        if preferred:
            parts += ["", "Preferred Qualifications"]
            for name in preferred[:6]:
                parts.append(
                    rng.choice(_PREFERRED_TEMPLATES).format(
                        s=self._surface(rng, name)
                    )
                )

        if rng.random() < 0.35:
            lo = rng.choice((4, 6, 8, 10, 12, 15, 18))
            parts += ["", f"Compensation: ₹{lo} - ₹{lo + rng.choice((3, 5, 8))} LPA"]

        parts += ["", "Benefits", rng.choice(_BOILERPLATE)]

        return RawPosting(
            external_id=f"syn-{profile.slug}-{month_index:02d}-{n:04d}",
            title=title,
            description="\n".join(parts),
            company=company,
            location=location,
            employment_type=rng.choice(_EMPLOYMENT),
            posted_at=posted,
            role_hint=profile.slug,
            url=None,
        )

    @staticmethod
    def _repost(rng: random.Random, original: RawPosting, posted: date) -> RawPosting:
        """A near-identical relist, as job boards produce constantly."""
        body = original.description
        if rng.random() < 0.5:
            body = body.replace("Requirements", "Requirements\nImmediate joiners preferred.", 1)
        return RawPosting(
            external_id=f"{original.external_id}-repost",
            title=original.title,
            description=body,
            company=original.company,
            location=original.location,
            employment_type=original.employment_type,
            posted_at=posted,
            role_hint=original.role_hint,
        )

    @staticmethod
    def _weighted_choice(rng: random.Random, pairs: tuple[tuple, ...]):
        total = sum(w for _, w in pairs)
        r = rng.random() * total
        upto = 0.0
        for value, weight in pairs:
            upto += weight
            if r <= upto:
                return value
        return pairs[-1][0]


register(SyntheticCorpusConnector())
