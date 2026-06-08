#!/bin/bash
set -e

DATA="${JARVIS_HOME:-/tmp/jarvis}"
mkdir -p "$DATA/memory" "$DATA/vault"

# Write Google credentials from env vars (JSON content, no base64)
# Set GOOGLE_TOKEN_JSON and GOOGLE_CLIENT_SECRET_JSON in Render → Environment
python3 - <<'PYEOF'
import os
from pathlib import Path

data = Path(os.environ.get("JARVIS_HOME", "/tmp/jarvis"))

for var, fname in [
    ("GOOGLE_TOKEN_JSON",          "google_token.json"),
    ("GOOGLE_CLIENT_SECRET_JSON",  "google_client_secret.json"),
]:
    content = os.environ.get(var, "").strip()
    if content:
        (data / fname).write_text(content)
        print(f"[startup] written {fname}")
    else:
        print(f"[startup] {var} not set — skipping")
PYEOF

uv run jarvis-web &
exec uv run jarvis-cron
