FROM python:3.12-slim

# Playwright/Chromium system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps first (layer cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Bake Chromium into the image (avoids slow runtime download)
RUN uv run playwright install chromium

COPY . .

# State directories — mount as volumes in production so data survives redeploys
RUN mkdir -p memory config

COPY scripts/start-backend.sh /start.sh
RUN chmod +x /start.sh

# Starts both jarvis-web (background) and jarvis-cron (foreground)
CMD ["/start.sh"]
