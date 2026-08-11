"""FastAPI application entry point.

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api import analyze, meta, profile, roles
from app.config import settings
from app.connectors import bootstrap
from app.database import init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hello-world")

DESCRIPTION = """
Job requirements intelligence: what employers actually ask for, extracted from
job postings and reported as frequencies rather than opinions.

**Reading the numbers.** Every percentage is `postings mentioning the skill /
relevant postings analysed`, after duplicate removal and relevance filtering.
Each statistic carries a `confidence` derived from sample size — a 90% figure
drawn from 8 postings is a much weaker claim than 40% drawn from 900.

**Data provenance.** `GET /api/sources` lists where postings came from. When any
source is `synthetic`, responses carry a caveat saying so: the default
development corpus is generated locally and is not evidence about the real job
market. See `docs/DATA_SOURCES.md`.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap()
    init_db()
    log.info("hello-world API ready (database: %s)", settings.database_url)
    yield


app = FastAPI(
    title="hello-world API",
    description=DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Profile-Token"],
)

app.include_router(meta.router)
app.include_router(roles.router)
app.include_router(analyze.router)
app.include_router(profile.router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Never leak SQL or schema details to a client."""
    log.exception("Database error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The database is unavailable. Please try again shortly."},
    )


@app.get("/", include_in_schema=False)
def index() -> dict[str, str]:
    return {
        "name": "hello-world",
        "tagline": settings.tagline,
        "docs": "/api/docs",
        "health": "/api/health",
    }
