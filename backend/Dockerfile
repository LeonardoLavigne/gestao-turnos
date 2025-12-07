# ==========================================
# Stage 1: Base (Dependências Comuns)
# ==========================================
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY pyproject.toml uv.lock ./

# Instalar dependências com uv
RUN uv sync --frozen --no-dev

# ==========================================
# Stage 2: Development
# ==========================================
FROM base AS development

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/bash appuser

COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY tests ./tests

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Instalar dev dependencies
RUN uv sync --frozen

RUN mkdir -p ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
