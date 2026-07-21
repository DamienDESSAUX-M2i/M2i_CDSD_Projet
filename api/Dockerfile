# ===
# Builder
# ===

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --frozen \
    --no-dev \
    --group api

COPY api/backend ./backend
COPY api/frontend ./frontend
COPY api/start.sh ./start.sh

# ===
# Runtime
# ===

FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsndfile1 \
        libcairo2 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/backend ./backend
COPY --from=builder /app/frontend ./frontend
COPY --from=builder /app/start.sh ./start.sh

RUN chmod +x start.sh

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 7860
EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=20s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["./start.sh"]