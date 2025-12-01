FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

# ✅ Aceitar UID/GID como build args (padrão 1000 se não passado)
ARG USER_ID=1000
ARG GROUP_ID=1000

# ✅ Criar usuário não-root com UID/GID do host
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/bash appuser

WORKDIR ${APP_HOME}

# Instalar dependências do sistema como root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app ./app

# ✅ Criar pasta data e dar ownership ao appuser
RUN mkdir -p ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

# ✅ Trocar para usuário não-root
USER appuser

ENV SQLITE_PATH=${APP_HOME}/data/gestao_turnos.db

CMD ["python", "-m", "app.run_all"]
