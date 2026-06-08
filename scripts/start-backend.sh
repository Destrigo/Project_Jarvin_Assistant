#!/bin/bash
set -e

# Use JARVIS_HOME if set (Render/Fly), otherwise default to /app (local Docker)
DATA="${JARVIS_HOME:-/tmp/jarvis}"
mkdir -p "$DATA/memory" "$DATA/vault"

# Decode Google credentials from base64 secrets (set on Render/Fly dashboard)
# Local: files already exist in config/, nothing to do
if [ -n "$GOOGLE_CLIENT_SECRET_JSON_B64" ]; then
    echo "$GOOGLE_CLIENT_SECRET_JSON_B64" | base64 -d > "$DATA/google_client_secret.json"
fi
if [ -n "$GOOGLE_TOKEN_JSON_B64" ]; then
    echo "$GOOGLE_TOKEN_JSON_B64" | base64 -d > "$DATA/google_token.json"
fi

# Start web API in background, cron+Telegram bot in foreground (PID 1)
uv run jarvis-web &
exec uv run jarvis-cron
