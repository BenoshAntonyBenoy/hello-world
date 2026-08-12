# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A job-requirements intelligence platform: it reads job postings, extracts what employers actually
ask for, and turns the result into a prioritised learning plan. A Python extraction/analytics
pipeline (`backend/`) and a React SPA (`frontend/`), joined either by a live FastAPI server or by
JSON frozen at build time.

## Commands

Two terminals. Python 3.11+, Node 18+. On Windows the interpreter is `.venv/Scripts/python`;
on macOS/Linux, `.venv/bin/python`.

```bash
# backend — first run
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/python manage.py seed        # tables + corpus + every statistic (~1 min)
.venv/Scripts/python -m uvicorn app.main:app --port 8010

# frontend
cd frontend
npm install
npm run dev            # http://localhost:5190, proxies /api to :8010
```

| Command | Purpose |
| --- | --- |
| `python manage.py seed --limit 300` | fast smoke test instead of the full corpus |
| `python manage.py recompute` | re-run analytics over postings already stored |
| `python manage.py stats` | what is currently in the database |
| `python manage.py sources` | registered connectors and which are enabled |
| `python manage.py reset --yes` | drop everything |
| `python export_static.py` | freeze every read-only response to `frontend/public/api/` |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run build` | typecheck + production build |

There is **no test suite**. Verification is `npm run build` (type errors are the main guard),
`manage.py stats` after a seed, and clicking through the running app.

To reproduce the deployed demo locally:

```bash
cd backend && python manage.py seed && python export_static.py
cd ../frontend && VITE_STATIC_DATA=true VITE_BASE_PATH=/hello-world/ npm run build
```

`.claude/launch.json` defines three preview targets: `helloworld-api` (:8010),
`helloworld-web` (:5190), `helloworld-static` (:5191).

## Architecture

### The dual API client — read this before touching the frontend

`src/lib/api.ts` exports `api` as **either** `liveApi` (fetches FastAPI) **or** `staticApi`
(fetches frozen JSON), chosen at build time by `VITE_STATIC_DATA`. Pages call `api.role(slug)`
without knowing which. Consequences:

- Any new endpoint must be implemented in **both** `api.ts` and `staticApi.ts`, and exported by
  `export_static.py`, or the GitHub Pages demo breaks while local dev looks fine.
- The skill-gap scoring in `staticApi.ts` is a **deliberate duplicate** of
  `backend/app/analytics/skillgap.py`. Change one, change the other — the weights and the
  frequency floor must stay identical.
- Two capabilities cannot survive the static build: `POST /api/analyze-job` (needs the Python
  extractor) and profile writes (fall back to local storage). `isStaticBuild` gates the UI so
  these explain themselves rather than failing.

### The taxonomy is the spine

`backend/app/extraction/taxonomy.py` declares every recognisable requirement exactly once
(~187 entries). Everything downstream keys off it:

- `slug` is **derived** from `canonical` (`+`→`plus`, `#`→`sharp`, `.`→`dot`, rest kebab-cased).
  Renaming a `canonical` silently changes its slug and orphans stored statistics, saved profiles
  and any URL pointing at it.
- `ensure_reference_data()` upserts the catalogue into the DB on every seed — reconciling, not
  duplicating. `validate_catalog()` aborts the seed if `data/roles.py` names a skill the taxonomy
  does not define.
- `strict` + `context_words` exist because short tokens (`R`, `Go`, `C`) match everywhere.
  Custom boundaries stop `C` matching inside `C++` and `Java` inside `JavaScript`; plain `\b`
  gets all three wrong.

### Pipeline

`ingestion.py` is the only module that knows all the pieces at once:

```
connector → normalize → dedupe → relevance → extract → persist → aggregate
```

Each posting is ingested inside a `begin_nested()` SAVEPOINT, so one malformed record rolls back
only itself. Near-duplicates are stored with `is_duplicate=True` for provenance and excluded from
every statistic; exact reposts are dropped.

### Connectors

`connectors/base.py` is the contract; every source declares a `kind` —
`api | licensed_dataset | public_feed | user_submitted | synthetic`. **There is deliberately no
`scraped` kind and one must not be added.** See `docs/DATA_SOURCES.md` for the accepted route to
each major board. The default corpus is `synthetic`: generated locally, fictional companies, real
prose that the real extractor then reads. Nothing is pre-computed.

### Analytics

`analytics/` — `frequency.py`, `trends.py`, `roadmap.py`, `skillgap.py`.

- Confidence is driven by **sample size**, not by how large a percentage looks.
- A skill is only labelled emerging/declining when the change exceeds **two standard errors**.
- The roadmap sorts by tier → `prerequisite_depth()` → frequency, then pulls in prerequisites the
  corpus also asks for even if they fell below the cutoff.
- Readiness is demand-weighted coverage, **not** a hiring probability.

## Conventions that matter here

**Honesty is a product requirement, not a tone.** Every figure carries its sample size; caveats are
*computed*, not written — `api/common.py:caveat_for()` returns the sample-data warning whenever any
contributing source is synthetic. Don't hardcode caveat copy in components; render what the API
returns. Don't imply a readiness score predicts hiring.

**Rounding parity.** `roadmap.py:_display_pct()` uses `floor(v + 0.5)` because Python's `:.0f`
rounds half to even and JS `Math.round` does not — without it, 36.5 renders as "36" and "37" in
adjacent elements. Keep any new percentage formatting matched to `frontend/src/lib/format.ts`.

**Colour comes from tokens.** `src/index.css` defines CSS variables for `:root` and `.dark`;
`tailwind.config.js` maps them to Tailwind colours. Add a token, never a raw hex, and check both
themes.

**Numbers are Indian-formatted** (`toLocaleString('en-IN')`, salaries in LPA) and columns of digits
use the `.tnum` class for tabular figures.

## Gotchas

- **Stop the API server before `manage.py reset`** — it holds the SQLite file open and the drop
  fails silently, making the next seed look like a corpus of duplicates.
- **Re-seeding on top of an existing corpus stores nothing** (every posting matches one already
  there). `seed` warns about this; `reset --yes` first if you meant to rebuild.
- **`frontend/public/api/` is gitignored and generated.** CI runs `seed` + `export_static.py` on
  every deploy so the published figures come from a fresh pipeline run. Never hand-edit those files.
- **The Pages workflow only runs on `main`**, and requires Settings → Pages → Source set to
  "GitHub Actions". While it is on "Deploy from a branch", Pages serves the README through Jekyll.
- `SEED_RANDOM_STATE` fixes the generated corpus, so the demo's numbers are reproducible across
  deploys. Changing it changes every published figure.
