# ==========================================
# Stage 1: Base
# ==========================================
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar arquivos de dependências
COPY pyproject.toml ./ 
# Nota: uv.lock pode não existir ainda para o bot se for novo, 
# mas se tivermos, descomentar. Vamos assumir apenas pyproject por hora ou gerar lock.
# Para garantir, vamos rodar sem lock se não existir, ou copiar se existir.
# Como é novo, vamos gerar o lock no build ou usar apenas pyproject.

# Instalar dependências
RUN uv sync


# ==========================================
# Stage 2: Development
# ==========================================
FROM base AS development

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/bash appuser

COPY src ./src

RUN chown -R appuser:appuser ${APP_HOME}

USER appuser

CMD ["uv", "run", "python", "-m", "src.main"]
