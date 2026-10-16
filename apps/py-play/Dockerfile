# --- Stage 1: Builder ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/py-play/pyproject.toml ./apps/py-play/
COPY packages/py-autobrowser/pyproject.toml ./packages/py-autobrowser/

RUN uv sync --frozen --no-dev --no-install-project --package play

# --- Stage 2: Runtime ---
FROM python:3.14-slim AS runner

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser apps/py-play/src/play /app/play

USER appuser

EXPOSE 7999

CMD ["fastapi", "run", "play/main.py", "--port", "7999", "--host", "0.0.0.0"]
