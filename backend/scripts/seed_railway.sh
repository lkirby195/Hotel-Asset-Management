#!/usr/bin/env bash
# Seed the Railway Postgres database with fictional demo data.
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:port/dbname ./scripts/seed_railway.sh
#
# Or pass the URL inline:
#   ./scripts/seed_railway.sh --database-url "postgresql://user:pass@host:port/dbname"
#
# To get your Railway DATABASE_URL:
#   railway variables --json | jq -r '.DATABASE_URL'

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

if [ -z "${DATABASE_URL:-}" ] && [ $# -eq 0 ]; then
    echo "ERROR: Set DATABASE_URL or pass --database-url <url>"
    echo ""
    echo "Example:"
    echo "  DATABASE_URL=postgresql://user:pass@host:5432/railway python scripts/seed_demo.py"
    exit 1
fi

python scripts/seed_demo.py "$@"
