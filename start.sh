#!/usr/bin/env bash
# start.sh — avvia backend e frontend in parallelo
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

trap 'kill $(jobs -p) 2>/dev/null; echo "Jarvis fermato."' EXIT INT TERM

echo "Avvio Jarvis..."
cd "$SCRIPT_DIR"
uv run jarvis-cron &

cd "$SCRIPT_DIR/frontend"
npm run dev &

echo "Backend:  http://localhost:8080"
echo "Frontend: http://localhost:3000"
echo "Premi Ctrl+C per fermare tutto."
wait
