# --- Stage 1: Builder ---
FROM python:3.14-slim AS builder 

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/py-play/pyproject.toml ./apps/py-play/
COPY packages/py-autobrowser/pyproject.toml ./packages/py-autobrowser/

RUN uv sync --frozen --no-dev --no-install-project --package play

# --- Stage 2: Runtime ---
FROM python:3.14-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    mosquitto-clients \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install OS dependencies for Chromium
RUN playwright install-deps chromium

# Create user with home directory so playwright can store browsers
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

COPY --chown=appuser:appuser apps/py-play/src/play /app/play

USER appuser

# Install Chromium browser binary as the user
RUN playwright install chromium

EXPOSE 7999

CMD ["fastapi", "run", "play/main.py", "--port", "7999", "--host", "0.0.0.0"]
