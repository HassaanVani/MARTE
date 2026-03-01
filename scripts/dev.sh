#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# Backend
echo "Starting backend on :8000..."
cd "$ROOT"
uv run uvicorn server.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Frontend
echo "Starting frontend on :5173..."
cd "$ROOT/frontend"
npm run dev -- --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "MARTE running:"
echo "  Frontend → http://localhost:5173"
echo "  Backend  → http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop."

wait
