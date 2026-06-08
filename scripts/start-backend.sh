#!/bin/bash
set -e
set +e  # credential decode failures must not abort startup

DATA="${JARVIS_HOME:-/tmp/jarvis}"
mkdir -p "$DATA/memory" "$DATA/vault"

# Render Secret Files (preferred) — upload via dashboard: Settings → Secret Files
# Path: /etc/secrets/google_client_secret.json and /etc/secrets/google_token.json
if [ -f /etc/secrets/google_client_secret.json ]; then
    cp /etc/secrets/google_client_secret.json "$DATA/google_client_secret.json"
elif [ -n "$GOOGLE_CLIENT_SECRET_JSON_B64" ]; then
    printf '%s' "$GOOGLE_CLIENT_SECRET_JSON_B64" | tr -d ' \n\r' | base64 -d > "$DATA/google_client_secret.json"
fi

if [ -f /etc/secrets/google_token.json ]; then
    cp /etc/secrets/google_token.json "$DATA/google_token.json"
elif [ -n "$GOOGLE_TOKEN_JSON_B64" ]; then
    printf '%s' "$GOOGLE_TOKEN_JSON_B64" | tr -d ' \n\r' | base64 -d > "$DATA/google_token.json"
fi

set -e  # re-enable for the actual app launch
uv run jarvis-web &
exec uv run jarvis-cron
