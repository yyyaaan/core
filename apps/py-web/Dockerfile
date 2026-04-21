# --- Stage 1: Builder ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/py-web/pyproject.toml ./apps/py-web/

RUN uv sync --frozen --no-dev --no-install-project --package web

# --- Stage 2: Runtime ---
FROM python:3.14-slim AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --chown=appuser:appuser apps/py-web/src/web /app/web

USER appuser

EXPOSE 8001

CMD ["fastapi", "run", "web/main.py", "--port", "8001", "--host", "0.0.0.0"]
