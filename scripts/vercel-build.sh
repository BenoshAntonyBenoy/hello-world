#!/usr/bin/env bash
# Vercel build: the same two-stage pipeline the GitHub Pages workflow runs.
#
#   seed  ->  export_static  ->  frontend/public/data/*.json  ->  vite build
#
# The corpus is generated and analysed here rather than committed, so the
# published figures always come from a fresh run of the real extractor. The
# SQLite file the seed produces is left in place: api/[...path].py bundles it
# read-only so the analyser can resolve roles and compare against the corpus.
set -euo pipefail

echo "── Python dependencies ──────────────────────────────"
# Vercel's Python is uv-managed and externally managed under PEP 668, so a bare
# `pip install` is refused. Prefer uv; fall back to a venv, then to overriding
# the marker, so this also runs on a plain machine.
# The build image's default python3 is 3.9, but the project needs 3.11+
# (pydantic-settings alone requires >=3.10). uv is present on the image and can
# fetch a suitable interpreter, so build against one it provisions rather than
# whatever happens to be on PATH.
PY=""
if command -v uv >/dev/null 2>&1; then
  echo "using uv with a provisioned Python 3.12"
  uv python install 3.12
  uv venv --python 3.12 .buildenv
  PY="$PWD/.buildenv/bin/python"
  uv pip install --python "$PY" --quiet -r backend/requirements.txt
else
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      "$candidate" -m venv .buildenv && PY="$PWD/.buildenv/bin/python" && break
    fi
  done
  [ -n "$PY" ] || { echo "no suitable Python found" >&2; exit 1; }
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -r backend/requirements.txt
fi
echo "building with $("$PY" --version)"

echo "── Build the corpus ─────────────────────────────────"
cd backend
"$PY" manage.py seed
echo "── Freeze the analysis to JSON ──────────────────────"
"$PY" export_static.py
cd ..

echo "── Build the site ───────────────────────────────────"
cd frontend
npm run build
cd ..

echo "── Done ─────────────────────────────────────────────"
ls -la frontend/dist | head -12
