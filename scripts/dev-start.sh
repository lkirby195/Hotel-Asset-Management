#!/usr/bin/env bash
# Start local development services (PostgreSQL, Redis, Backend, Frontend)
# Requires: portable PostgreSQL and Redis installed in ~/.local/

set -e

export PATH="/c/Users/LoganKirby/.local/pgsql/pgsql/bin:/c/Users/LoganKirby/.local/node:$PATH"

PG_DATA="/c/Users/LoganKirby/.local/pgsql/data"
PG_LOG="/c/Users/LoganKirby/.local/pgsql/pg.log"
REDIS_BIN="/c/Users/LoganKirby/.local/redis/redis-server.exe"
PROJECT_DIR="/c/Users/LoganKirby/hotel-asset-management"

echo "=== Starting PostgreSQL ==="
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "PostgreSQL already running"
else
    pg_ctl -D "$PG_DATA" -l "$PG_LOG" start
    sleep 2
    echo "PostgreSQL started"
fi

echo "=== Starting Redis ==="
if "$(/c/Users/LoganKirby/.local/redis/redis-cli.exe)" ping >/dev/null 2>&1; then
    echo "Redis already running"
else
    "$REDIS_BIN" --daemonize no --port 6379 &
    sleep 1
    echo "Redis started"
fi

echo "=== Starting Backend (FastAPI) ==="
cd "$PROJECT_DIR/backend"
source .venv/Scripts/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
sleep 2
echo "Backend started (PID: $BACKEND_PID)"

echo "=== Starting Frontend (Next.js) ==="
cd "$PROJECT_DIR/frontend"
npx next dev --port 3000 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "=== All services running ==="
echo "  Backend:  http://localhost:8000  (API: http://localhost:8000/api/v1)"
echo "  Frontend: http://localhost:3000"
echo "  Health:   http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any child to exit
wait
