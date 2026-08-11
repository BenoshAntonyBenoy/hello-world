#!/usr/bin/env python
"""Command-line entry point for database and ingestion tasks.

    python manage.py seed          # create tables, ingest, compute analytics
    python manage.py recompute     # re-run analytics over existing postings
    python manage.py reset         # drop everything and start over
    python manage.py stats         # print what is currently in the database
    python manage.py sources       # list registered connectors
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from sqlalchemy import func, select

from app.config import settings
from app.connectors import bootstrap, enabled_connectors, all_connectors
from app.database import Base, SessionLocal, engine, init_db
from app.ingestion import ensure_reference_data, ingest, recompute_analytics
from app.models import Job, Role, RoleSkillStatistic, Skill, SkillTrend

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("manage")


def cmd_seed(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    bootstrap()
    init_db()

    with SessionLocal() as db:
        log.info("Loading reference data (taxonomy + role catalogue)…")
        ensure_reference_data(db)
        db.commit()

        connectors = enabled_connectors()
        if not connectors:
            log.error("No connectors enabled. Set ENABLED_CONNECTORS in .env")
            return 1

        for connector in connectors:
            healthy, message = connector.health_check()
            if not healthy:
                log.warning("Skipping %s: %s", connector.key, message)
                continue
            log.info("Ingesting from %s…", connector.key)
            report = ingest(db, connector, limit=args.limit)
            log.info("  %s", report.summary())
            for error in report.errors[:5]:
                log.warning("  error: %s", error)

            # Re-seeding on top of an existing corpus looks like a successful
            # run that stored nothing, which is confusing enough to call out.
            if report.fetched and not report.stored:
                log.warning(
                    "  Nothing was stored — every posting matched one already in "
                    "the database. Run 'python manage.py reset --yes' first if you "
                    "meant to rebuild the corpus. (Stop the API server too: it "
                    "holds the SQLite file open.)"
                )

        log.info("Computing statistics and trends…")
        results = recompute_analytics(db)
        for slug, counts in sorted(results.items()):
            log.info(
                "  %-30s %3d skills  %4d trend points",
                slug, counts["skills"], counts["trend_points"],
            )

    log.info("Done in %.1fs", time.perf_counter() - started)
    return 0


def cmd_recompute(_: argparse.Namespace) -> int:
    bootstrap()
    with SessionLocal() as db:
        results = recompute_analytics(db)
        for slug, counts in sorted(results.items()):
            log.info("%-30s %3d skills  %4d trend points",
                     slug, counts["skills"], counts["trend_points"])
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        answer = input(f"Drop all tables in {settings.database_url}? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            log.info("Aborted.")
            return 1
    Base.metadata.drop_all(bind=engine)
    log.info("Dropped all tables.")
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    bootstrap()
    with SessionLocal() as db:
        total_jobs = db.scalar(select(func.count()).select_from(Job)) or 0
        countable = db.scalar(
            select(func.count()).select_from(Job)
            .where(Job.is_relevant.is_(True))
            .where(Job.is_duplicate.is_(False))
        ) or 0
        print(f"\nDatabase: {settings.database_url}")
        print(f"  skills in taxonomy : {db.scalar(select(func.count()).select_from(Skill))}")
        print(f"  roles              : {db.scalar(select(func.count()).select_from(Role))}")
        print(f"  postings (total)   : {total_jobs}")
        print(f"  postings (counted) : {countable}")
        print(f"  statistics rows    : {db.scalar(select(func.count()).select_from(RoleSkillStatistic))}")
        print(f"  trend points       : {db.scalar(select(func.count()).select_from(SkillTrend))}\n")

        rows = db.execute(
            select(Role.title, func.count(Job.id))
            .join(Job, Job.role_id == Role.id)
            .where(Job.is_relevant.is_(True))
            .where(Job.is_duplicate.is_(False))
            .group_by(Role.title)
            .order_by(func.count(Job.id).desc())
        ).all()
        for title, count in rows:
            print(f"  {title:<34} {count:>5}")
        print()
    return 0


def cmd_sources(_: argparse.Namespace) -> int:
    bootstrap()
    print()
    for connector in all_connectors():
        d = connector.descriptor
        enabled = "enabled" if d.key in settings.connector_list else "available"
        print(f"  {d.key:<18} {d.kind:<18} [{enabled}]  {d.name}")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="manage.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="create tables, ingest and compute analytics")
    p_seed.add_argument("--limit", type=int, default=None,
                        help="cap postings per connector (useful for a fast smoke test)")
    p_seed.set_defaults(func=cmd_seed)

    sub.add_parser("recompute", help="recompute analytics only").set_defaults(func=cmd_recompute)

    p_reset = sub.add_parser("reset", help="drop all tables")
    p_reset.add_argument("--yes", action="store_true", help="skip confirmation")
    p_reset.set_defaults(func=cmd_reset)

    sub.add_parser("stats", help="show database contents").set_defaults(func=cmd_stats)
    sub.add_parser("sources", help="list registered connectors").set_defaults(func=cmd_sources)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
