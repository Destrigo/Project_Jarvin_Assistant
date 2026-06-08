#!/usr/bin/env bash
# Stampa i secret da copiare nel dashboard di Render
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Copia questi valori nelle Environment Variables di Render ==="
echo ""

source .env
echo "MISTRAL_API_KEY=$MISTRAL_API_KEY"
echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN"
echo "TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID"
echo ""
echo "GOOGLE_CLIENT_SECRET_JSON_B64=$(base64 -w0 config/google_client_secret.json)"
echo "GOOGLE_TOKEN_JSON_B64=$(base64 -w0 config/google_token.json)"
