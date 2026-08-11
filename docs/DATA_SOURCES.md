# Where the job data comes from

The product's credibility rests entirely on this question, so it gets its own
document. The short version: **hello-world does not scrape job boards.** It
ingests through a connector layer, and every connector has to declare the legal
basis on which it obtains data.

> ⚠️ Terms of service change. Everything below is a starting point for your own
> diligence, not legal advice, and not a claim about any platform's current
> terms. Re-read the actual agreement before you integrate anything.

---

## The rule the codebase enforces

`app/connectors/base.py` requires every source to declare a `kind`:

| `kind` | Meaning |
| --- | --- |
| `api` | Official, documented API used within its terms |
| `licensed_dataset` | Data obtained under a commercial or research licence |
| `public_feed` | An endpoint the publisher intends for public consumption |
| `user_submitted` | A posting the user supplied themselves |
| `synthetic` | Generated sample data (development only) |

There is deliberately no `scraped` kind. A connector that would need to defeat
authentication, ignore `robots.txt`, rotate IPs, or bypass anti-bot measures
does not belong in this repository — not as a stretch goal, not behind a flag.

Beyond the legal exposure, scraped data is *bad data*: you get whatever the
anti-bot system decided to serve a suspicious client, silently biased, with no
recourse when it breaks.

---

## Routes worth pursuing, roughly in order of effort

### 1. ATS public job boards — the best starting point

Most companies publish their own openings through an applicant tracking system,
and several ATS vendors expose each customer's board as a public JSON endpoint
intended for exactly this kind of consumption. Greenhouse, Lever, Ashby,
SmartRecruiters and Workday all have some form of public board interface.

Why this route is strong:

- The publisher **wants** these read — that is the point of a public board
- Stable, structured JSON rather than parsed HTML
- No licensing negotiation for the public endpoints
- Attribution and linking back to the original listing is straightforward

The tradeoff is coverage: you get one company at a time, so you need a list of
employers to enumerate. For an India-focused product, a few hundred well-chosen
tech employers gets you a genuinely useful corpus.

**Do still check** each vendor's API terms and honour their rate limits.

### 2. Job-search APIs with published terms

Several aggregators run documented APIs with free or low-cost tiers for
non-commercial use. Adzuna and Jooble are commonly cited examples. These give
broad coverage cheaply, at the cost of less structured descriptions and
attribution requirements you must honour.

### 3. Government and open data

- **National Career Service (NCS)** — India's government employment portal
- **data.gov.in** — periodically publishes labour and employment datasets
- **Periodic Labour Force Survey (PLFS)** — official employment statistics,
  useful for validating that your corpus is not wildly unrepresentative

Lower volume and often lagging, but authoritative and unambiguously usable —
which makes it excellent for sanity-checking whatever else you ingest.

### 4. Partner and licensed access to the large boards

LinkedIn and Naukri are the two sources users will ask about first. Both
restrict automated extraction in their user agreements, and both have partner
or enterprise programmes that are the legitimate route in. Expect these to
involve a commercial conversation, a review process, and constraints on what
you may display and retain.

Plan the product so it is useful **without** them, and treat access as an
upgrade rather than a dependency. That is precisely why the connector layer
exists.

### 5. User-submitted descriptions

Already implemented (`app/connectors/user_submitted.py`). A user pasting a
posting they are looking at is unambiguously fine, needs no negotiation, and
delivers immediate value through `POST /api/analyze-job`.

Note the deliberate limitation: submissions are **not** merged into published
role statistics. Anyone could otherwise shift the numbers by pasting text
repeatedly. Promotion into the corpus should be a reviewed action.

---

## What ships today

The default configuration enables only `mock_dataset` — a locally generated,
deterministic corpus of fictional companies (`app/connectors/synthetic.py`).

It exists so the application is fully explorable before any feed is connected.
Two properties make it defensible:

1. **Nothing is pre-computed.** The generator writes prose; the real extractor
   reads that prose and recomputes every number. Swapping in a real connector
   changes the inputs, not the pipeline.
2. **Nothing impersonates a real employer.** Company names are generated from
   neutral word pools, and every posting is stamped `synthetic` so the UI
   labels it as sample data.

**Do not present statistics derived from this corpus as market fact.** They
demonstrate that the system works; they are not evidence about the job market.

---

## Adding a real connector

```python
from app.connectors.base import JobDataConnector, RawPosting, SourceDescriptor
from app.connectors.registry import register


class GreenhouseBoardConnector(JobDataConnector):
    key = "greenhouse"

    def __init__(self, board_tokens: list[str]) -> None:
        self._boards = board_tokens

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            key=self.key,
            name="Greenhouse public job boards",
            kind="public_feed",
            base_url="https://boards-api.greenhouse.io",
            terms_url="https://www.greenhouse.io/legal",
        )

    def fetch(self, role_slugs=None, limit=None):
        for token in self._boards:
            for posting in self._fetch_board(token):
                yield RawPosting(...)


register(GreenhouseBoardConnector(board_tokens=[...]))
```

Then add `greenhouse` to `ENABLED_CONNECTORS` and re-run ingestion. Nothing
downstream — normalization, extraction, statistics, the API, the UI — needs to
change.

---

## Retention and attribution checklist

Whatever source you add, these are the recurring obligations:

- [ ] Link back to the original posting; never present a listing as your own
- [ ] Honour stated rate limits and cache aggressively
- [ ] Respect deletion — if a posting is pulled, stop showing it
- [ ] Store `source`, `url` and `ingested_at` on every row (the schema does)
- [ ] Check whether the terms permit **derived statistics** as well as display;
      these are sometimes governed separately
- [ ] Keep the raw text only as long as you need it to recompute extractions
