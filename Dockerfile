# ==========================================
# Stage 1: Base (Dependências Comuns)
# ==========================================
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Development (Com Fix de Permissões)
# ==========================================
FROM base AS development

# Aceitar UID/GID do host para evitar problemas de permissão
ARG USER_ID=1000
ARG GROUP_ID=1000

# Criar usuário com UID/GID específicos
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/bash appuser

# Copiar código (será sobrescrito pelo bind mount, mas útil para cache)
COPY app ./app

# Criar pasta data e ajustar permissões
RUN mkdir -p ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

USER appuser

ENV SQLITE_PATH=${APP_HOME}/data/gestao_turnos.db

CMD ["python", "-m", "app.run_all"]

# ==========================================
# Stage 3: Production (Limpo e Seguro)
# ==========================================
FROM base AS production

# Copiar código fonte e migrations
COPY app ./app
COPY migrations ./migrations
# COPY alembic.ini .  <-- Descomente se já tiver o arquivo gerado

# Criar usuário não-root padrão para produção
RUN useradd -m appuser && \
    mkdir -p ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

# Script de entrada para aplicar migrations automaticamente
RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    # Verificar se alembic.ini existe antes de tentar rodar migrations\n\
    if [ -f "alembic.ini" ]; then\n\
    echo "🔄 Aplicando migrations..."\n\
    alembic upgrade head\n\
    else\n\
    echo "⚠️  alembic.ini não encontrado, pulando migrations..."\n\
    fi\n\
    \n\
    echo "🚀 Iniciando aplicação..."\n\
    exec python -m app.run_all' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
