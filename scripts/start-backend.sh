#!/bin/bash
# Jarvis è disattivato. Per riattivare, ripristina l'ultimo commit funzionante:
#   git revert HEAD && git push
set -e

echo "[jarvis] Modalità offline — il servizio risponde solo a /health"

python3 - << 'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"offline"}')
        else:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"Jarvis offline"}')
    def do_POST(self):
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"detail":"Jarvis offline"}')

print("[jarvis] Listening on :8080")
HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
EOF
