# hello-world

**Learn what the industry actually wants.**

A job-requirements intelligence platform. It reads job postings, extracts what
employers actually ask for, and turns the result into a prioritised learning
plan — so a student can prepare for the job rather than the syllabus.

```
Job data sources → Connectors → Normalization → Requirement extraction
      → Skill classification → Frequency & trend analysis → Dashboard
```

---

## Quick start

Two terminals. Python 3.11+ and Node 18+.

**1 — Backend**

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/python manage.py seed
.venv/Scripts/python -m uvicorn app.main:app --port 8010
```

On macOS/Linux the interpreter is `.venv/bin/python`.

`manage.py seed` creates the tables, generates the sample corpus, runs it
through the real extraction pipeline and computes every statistic. It takes
about a minute and prints what it did.

**2 — Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5190**. The dev server proxies `/api` to port 8010, so
there is no CORS setup to do.

API docs are at **http://localhost:8010/api/docs**.

---

## ⚠️ About the numbers you will see

The default configuration runs on a **synthetic corpus generated on your
machine**. Companies in it are fictional and the postings are not real
vacancies.

It exists so the product is fully explorable before a licensed data feed is
connected, and it is honest about two things:

- **Nothing is pre-computed.** The generator writes prose; the real extractor
  reads that prose and recomputes every percentage. Swapping in a real
  connector changes the inputs, not the pipeline.
- **Nothing impersonates a real employer.** Fabricating a listing and
  attributing it to a real company would be inventing a record about that
  company.

Every affected API response carries a caveat, and the UI labels sample
postings. **Do not present these figures as evidence about the job market.**
See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for the legitimate routes to
real data.

---

## Deploying the demo to GitHub Pages

**Pages serves static files, so it cannot run FastAPI.** Publishing the repo as
it stands gets you either a Jekyll-rendered README or, if you point Pages at
`frontend/`, a blank screen — `frontend/index.html` is a Vite *source* template
that loads `/src/main.tsx`, which no browser can execute.

The workflow in [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)
solves that by building the corpus in CI, freezing the analysis to JSON, and
publishing a static bundle that reads those files:

```
manage.py seed  →  export_static.py  →  frontend/public/api/*.json
                                     →  vite build (VITE_STATIC_DATA=true)
```

### One-time setup

> **Settings → Pages → Build and deployment → Source → "GitHub Actions"**

While that is still set to *Deploy from a branch*, Pages serves the repository
root through Jekyll — which is exactly why the README shows up instead of the
app — and the workflow's deploy step will fail.

### What works in the static build, and what does not

| | Static demo | Running locally |
| --- | --- | --- |
| Role dashboards, skills, roadmaps, trends, listings | ✅ | ✅ |
| Search | ✅ client-side | ✅ |
| Skill profile | ✅ local storage only | ✅ anonymous token |
| Skill gap | ✅ computed in-browser | ✅ |
| **Analyse a pasted JD** | ❌ needs the Python extractor | ✅ |

The analyser page says so plainly rather than offering a button that fails.

Nothing is hand-written into those JSON files: CI runs `manage.py seed` and the
real extractor on every deploy, so the published figures come from a fresh run
of the pipeline rather than a blob committed months ago. `frontend/public/api/`
is gitignored for that reason.

### Building it yourself

```bash
cd backend && python manage.py seed && python export_static.py
cd ../frontend
VITE_STATIC_DATA=true VITE_BASE_PATH=/hello-world/ npm run build
npx vite preview --port 5191     # then open /hello-world/
```

On Windows PowerShell, set the two variables with `$env:NAME='value'` first.

`VITE_BASE_PATH` must match where the site is served. `/hello-world/` for a
GitHub project page, `/` for a domain root — the workflow derives it from the
repository name automatically.

---

## What is here

```
backend/
  app/
    connectors/      Job Data Connector layer — one class per source
      base.py          the contract every source implements
      registry.py      registration and lookup
      synthetic.py     the sample corpus generator (development only)
      user_submitted.py  postings a user pastes in
    extraction/      Requirement extraction engine
      taxonomy.py      187 canonical requirements, aliases, tiers, prerequisites
      normalizer.py    cleaning, section splitting, experience/education/salary
      matcher.py       boundary-aware matching, ambiguity and overlap handling
      dedupe.py        simhash near-duplicate detection, relevance scoring
      extractor.py     the pipeline that ties those together
      llm.py           optional LLM pass for uncovered phrasing (off by default)
    analytics/       frequency.py, trends.py, roadmap.py, skillgap.py
    api/             FastAPI routers
    data/roles.py    role catalogue + demand profiles for the generator
    models.py        SQLAlchemy models (10 tables)
    ingestion.py     connector → extract → dedupe → persist → aggregate
  sql/schema.sql     PostgreSQL DDL (the production target)
  manage.py          seed / recompute / reset / stats / sources
frontend/
  src/pages/         landing, search, role dashboard, skills, roadmap,
                     listings, trends, profile, skill gap, analyse, about
  src/components/    UI primitives, charts, search, layout
  src/lib/           API client, types, hooks, formatting
docs/DATA_SOURCES.md Where data may legally come from, and how to add a source
```

---

## How a number gets made

This is the part that matters, so it is worth being precise about.

**1. Collect.** Postings arrive through a connector. Every connector declares
its `kind` — `api`, `licensed_dataset`, `public_feed`, `user_submitted` or
`synthetic` — so the legal basis of each row is auditable. There is
deliberately no `scraped` kind.

**2. Deduplicate.** Exact reposts are dropped. Near-identical relists are
detected with a 64-bit simhash over token shingles, stored for provenance and
excluded from every statistic. Counting one company's listing eight times is
how you accidentally report their stack as an industry trend.

**3. Filter relevance.** Postings are scored on title agreement and whether
they contain the role's core skills at all. A mis-titled sales listing cannot
pollute a Data Analyst breakdown.

**4. Extract.** Each posting is split into sections, so `Requirements` and
`Preferred Qualifications` are distinguished rather than flattened. Then:

- **Synonyms collapse.** `React.js`, `ReactJS`, `React JS` → **React**.
  `Amazon Web Services` → **AWS**.
- **Boundaries are custom.** `C` does not match inside `C++`; `Java` does not
  match inside `JavaScript`; `SQL` does not match inside `MySQL`. Plain `\b`
  gets all three wrong.
- **Ambiguous tokens need context.** `R`, `Go` and `C` only count when a
  supporting word is nearby, and known traps are excluded — `R&D` is not the R
  language, `go-to-market` is not Go, and "reporting to the leadership team"
  is not a request for leadership skills.
- **Longest match wins.** `Communication Protocols` no longer also increments
  `Communication`.
- **Degree lines are excluded from skill counts.** "B.Tech in Statistics"
  states a field of study, not that the employer wants statistical analysis as
  a working skill. The degree is still captured separately.

**5. Count.**

```
frequency = postings mentioning the skill / relevant postings analysed × 100
```

Every figure carries a **confidence** driven by sample size, not by how large
the percentage looks. 90% of 8 postings is a far weaker claim than 40% of 900.

**6. Detect trends.** Monthly frequency series per skill. A skill is only
labelled *emerging* or *declining* when the change exceeds **two standard
errors** for the number of postings observed. Without that test, a skill
sitting flat at 50% with 15 postings a month routinely swings ±10pp and gets
announced as a trend.

**7. Sequence.** Demand becomes a learning path ordered by prerequisite depth,
so nothing is recommended before its foundation. Sorting by frequency alone
would tell a beginner to start with Kubernetes.

---

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service and data status |
| `GET` | `/api/search?q=` | Search roles |
| `GET` | `/api/roles` | All analysed roles |
| `GET` | `/api/roles/{role}` | Full analysis for a role |
| `GET` | `/api/roles/{role}/skills` | Every requirement, grouped |
| `GET` | `/api/roles/{role}/trends` | Monthly series + direction |
| `GET` | `/api/roles/{role}/roadmap` | Ordered learning path |
| `GET` | `/api/roles/{role}/jobs` | The postings behind the analysis |
| `POST` | `/api/analyze-job` | Extract from a pasted description |
| `GET` | `/api/skills` | The requirement vocabulary |
| `GET` | `/api/sources` | Data provenance |
| `GET` | `/api/profile` | Read the anonymous profile |
| `POST` | `/api/profile/skills` | Replace the skill list |
| `DELETE` | `/api/profile` | Delete the profile and all its data |
| `GET` | `/api/profile/skill-gap/{role}` | Readiness and gaps |

`{role}` accepts a slug, an exact title, or an alias — `ml engineer` resolves
to `AI/ML Engineer`.

Profile endpoints take an `X-Profile-Token` header.

---

## Configuration

Everything in `backend/.env.example` has a working default.

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./helloworld.db` | See PostgreSQL below |
| `CORS_ORIGINS` | `localhost:5190,…` | Comma-separated |
| `ENABLED_CONNECTORS` | `mock_dataset` | See `manage.py sources` |
| `SEED_POSTINGS_PER_ROLE` | `180` | Corpus size |
| `SEED_RANDOM_STATE` | `20260811` | Same seed → same corpus |
| `SEED_HISTORY_MONTHS` | `12` | Months of history for trends |
| `CONFIDENCE_HIGH_MIN_POSTINGS` | `150` | Confidence thresholds |
| `LLM_EXTRACTION_ENABLED` | `false` | See below |

### PostgreSQL

SQLite is the default only so the project runs with zero setup. The schema is
written to be Postgres-compatible and `sql/schema.sql` is the canonical DDL.

```bash
pip install "psycopg[binary]"
# .env
DATABASE_URL=postgresql+psycopg://helloworld:helloworld@localhost:5432/helloworld
```

Then `python manage.py seed`. Nothing else changes.

### Optional LLM extraction

The pipeline is deterministic and offline by default, and that is the right
default for this product: if the same corpus yields different percentages on
different runs, the percentages stop meaning anything.

`app/extraction/llm.py` defines the opt-in path. It sends the model only the
*residue* — requirement-shaped sentences containing no known skill — so cost
scales with gaps in the vocabulary rather than with corpus size. Anything the
model proposes is a **candidate for the taxonomy**, surfaced for review, never
silently counted in published statistics. The network call is intentionally
left unimplemented; see the module for what to wire up.

---

## Privacy

- No accounts, no email addresses, no passwords, no third-party tracking.
- A profile is an opaque token your browser generates plus a list of skills you
  selected. Nothing else is stored.
- `DELETE /api/profile` removes every row. The UI exposes it as "Delete my data".
- Pasted job descriptions are buffered in memory and are **not** merged into
  published statistics — otherwise anyone could move the numbers by pasting the
  same text repeatedly.

---

## What the numbers do not mean

The readiness score is **demand-weighted coverage**: how much of a role's
commonly requested skill set you currently cover. It is **not** a probability of
being hired. It knows nothing about interviews, portfolio, referrals, or
whether anyone is hiring. Every response carries that disclaimer and the UI
shows it — a career tool that implies a guarantee does real harm to someone
making a real decision.

Two more caveats worth keeping in view:

- **Frequency is not importance.** A skill in 90% of postings is usually
  necessary but rarely sufficient. The rare one in 8% may be what
  differentiates you.
- **Coverage is partial.** No corpus sees every posting. Small samples are
  labelled as such rather than quietly rounded up.

---

## Commands

```bash
python manage.py seed          # create tables, ingest, compute analytics
python manage.py seed --limit 300   # fast smoke test
python manage.py recompute     # re-run analytics over existing postings
python manage.py stats         # what is currently in the database
python manage.py sources       # registered connectors
python manage.py reset --yes   # drop everything
```

Stop the API server before `reset` — it holds the SQLite file open, and the
delete will otherwise fail silently and make the next seed look like a corpus
of duplicates.

```bash
python export_static.py        # freeze the analysis for a static deploy
```

```bash
npm run typecheck   # frontend
npm run build       # typecheck + production build
```

---

## Roadmap

**Phase 1 — done.** Landing page, role search, connector architecture, JD
parsing, skill extraction, frequency analysis, interactive dashboard, learning
recommendations.

**Phase 2 — done.** Skill profile, gap analysis, job listings, trend analysis.

**Phase 3 — next.** Real data connectors (start with ATS public boards — see
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)), longer historical baselines,
per-city and per-seniority breakdowns, wiring up the optional LLM pass for
taxonomy expansion.

If the JD analyser needs to work on the public demo, the static build is not
the way — host the backend somewhere that runs Python (Render, Railway, Fly, or
Vercel serverless) and point the frontend at it with `VITE_API_BASE`. The
client already supports that: `VITE_STATIC_DATA` simply stays unset.
