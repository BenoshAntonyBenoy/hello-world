#!/usr/bin/env python
"""Export every read-only API response as static JSON.

GitHub Pages serves files, not Python. This script freezes the analysis into
a tree of JSON documents that the frontend can fetch directly, so the deployed
demo shows real extracted data with no backend running.

    python manage.py seed          # build the corpus first
    python export_static.py        # then freeze it

Output lands in ``frontend/public/api/`` and is copied into the build by Vite.
It is gitignored: CI regenerates it on every deploy, so the published numbers
always come from a fresh run of the real pipeline rather than a stale blob
committed months ago.

What is *not* exported, because it cannot be:

``POST /api/analyze-job``
    Needs the Python extractor. The static build disables that page and says so.

``/api/profile*``
    Writes. The static build keeps the profile in the browser's local storage
    instead, which is arguably the more honest version of "we store nothing".
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.api import meta, roles as roles_api
from app.config import BACKEND_DIR
from app.connectors import bootstrap
from app.database import SessionLocal
from app.models import Role

OUT_DIR = BACKEND_DIR.parent / "frontend" / "public" / "api"

# Deliberately larger than the interactive defaults: the static build paginates
# and filters client-side, so it wants the full set in one document.
TREND_LIMIT = 25
JOBS_LIMIT = 60


def _write(path: Path, payload: Any) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        data = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in payload
        ]
    else:
        data = payload
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def main() -> int:
    bootstrap()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    written = 0
    total_bytes = 0

    with SessionLocal() as db:
        role_rows = db.scalars(select(Role).order_by(Role.slug)).all()
        if not role_rows:
            print(
                "No roles in the database. Run 'python manage.py seed' first.",
                file=sys.stderr,
            )
            return 1

        total_bytes += _write(OUT_DIR / "health.json", meta.health(db=db))
        total_bytes += _write(OUT_DIR / "sources.json", meta.list_sources(db=db))
        total_bytes += _write(
            OUT_DIR / "skills.json",
            meta.list_skills(q=None, category=None, limit=1000, db=db),
        )
        total_bytes += _write(OUT_DIR / "roles.json", roles_api.list_roles(db=db))
        written += 4

        for role in role_rows:
            slug = role.slug
            base = OUT_DIR / "roles" / slug

            total_bytes += _write(
                OUT_DIR / "roles" / f"{slug}.json",
                roles_api.get_role(role=slug, db=db),
            )
            total_bytes += _write(
                base / "skills.json",
                roles_api.get_role_skills(role=slug, min_frequency=0.0, db=db),
            )
            total_bytes += _write(
                base / "trends.json",
                roles_api.get_role_trends(role=slug, limit=TREND_LIMIT, db=db),
            )
            total_bytes += _write(
                base / "roadmap.json",
                roles_api.get_role_roadmap(role=slug, profile_token=None, db=db),
            )
            total_bytes += _write(
                base / "jobs.json",
                roles_api.get_role_jobs(role=slug, limit=JOBS_LIMIT, offset=0, db=db),
            )
            written += 5
            print(f"  {slug}")

    print(
        f"\nWrote {written} files ({total_bytes / 1024:.0f} KB) to "
        f"{OUT_DIR.relative_to(BACKEND_DIR.parent)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
