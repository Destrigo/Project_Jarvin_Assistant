#!/usr/bin/env bash
# install.sh — first-time setup + enable systemd autostart
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Jarvis — Setup ==="

# 1. Python deps
echo "[1/5] Installing Python dependencies..."
cd "$SCRIPT_DIR"
uv sync

# 2. Node deps + build frontend
echo "[2/5] Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install
npm run build

# 3. Create .env if missing
cd "$SCRIPT_DIR"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[3/5] Created .env — edit it with your API keys before starting"
else
    echo "[3/5] .env already exists, skipping"
fi

# 4. Create Obsidian vault directory
VAULT="${OBSIDIAN_VAULT:-$HOME/Documents/Jarvis}"
VAULT="${VAULT/#\~/$HOME}"
mkdir -p "$VAULT/Memoria" "$VAULT/Conversazioni"
echo "[4/5] Obsidian vault ready: $VAULT"

# 5. Enable systemd services
echo "[5/5] Enabling systemd autostart..."
systemctl --user daemon-reload
systemctl --user enable jarvis-backend.service
systemctl --user enable jarvis-frontend.service
loginctl enable-linger "$USER" 2>/dev/null || true

echo ""
echo "=== Done! ==="
echo ""
echo "Fill in .env, then:"
echo "  uv run python -c \"from integrations.gmail import _service; _service()\""
echo "  (first-time Google login)"
echo ""
echo "Start now:    systemctl --user start jarvis-backend jarvis-frontend"
echo "Check status: systemctl --user status jarvis-backend jarvis-frontend"
echo "Logs:         journalctl --user -u jarvis-backend -f"
echo "Frontend:     http://localhost:3000"
