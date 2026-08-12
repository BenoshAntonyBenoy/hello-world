"""Vercel serverless entry point for the job-ad analyser.

Only the analyser lives here. Everything else the site shows — role dashboards,
skills, roadmaps, trends, listings — is frozen to JSON at build time and served
statically, so it needs no server at all. The analyser cannot be, because it
runs the Python taxonomy matcher and section parser over text the visitor
supplies at request time.

The database is bundled read-only. `scripts/vercel-build.sh` runs the real seed
during the build, so the analyser resolves roles and compares against the same
corpus the rest of the site reports on. Nothing here writes: the pasted
description is buffered in memory and never merged into published statistics.

Named `[...path].py` so Vercel routes every /api/* request here with the
original path intact, rather than rewriting it to a single endpoint.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Must be set before app.config is imported, since settings are read at import.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{BACKEND / 'helloworld.db'}")

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.api import analyze  # noqa: E402
from app.connectors import bootstrap  # noqa: E402
from app.schemas import AnalyzeJobResponse  # noqa: E402

bootstrap()

app = FastAPI(
    title="hello-world analyser",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(analyze.router)

# Vercel's catch-all should hand over the original path, but if it ever strips
# the /api prefix the endpoint would 404 with no obvious cause. Registering the
# unprefixed path too costs one line and removes that failure mode.
app.add_api_route(
    "/analyze-job",
    analyze.analyze_job,
    methods=["POST"],
    response_model=AnalyzeJobResponse,
    include_in_schema=False,
)


@app.get("/api/health", include_in_schema=False)
@app.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    """Cheap check that the function booted and can see its database."""
    db_file = BACKEND / "helloworld.db"
    return JSONResponse(
        {
            "status": "ok",
            "analyser": "available",
            "database": "bundled" if db_file.exists() else "missing",
        }
    )
