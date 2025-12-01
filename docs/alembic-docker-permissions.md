# Guia: Alembic no Docker sem Problemas de Permissão

## 🎯 Problema

Quando você roda Alembic dentro do Docker:
- ❌ Container cria arquivos como `root` (UID 0)
- ❌ No host, você não consegue editar (permission denied)
- ❌ Ou container não consegue escrever em pastas do host

## ✅ Solução: Rodar Container com Seu UID/GID

### 1. Atualizar Dockerfile

```dockerfile
# Dockerfile

FROM python:3.13-slim

# Criar usuário não-root com UID/GID passados por build args
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar como root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app ./app

# ✅ Mudar ownership para appuser
RUN chown -R appuser:appuser /app

# ✅ Trocar para usuário não-root
USER appuser

CMD ["python", "-m", "app.run_all"]
```

### 2. Atualizar docker-compose.yml

```yaml
# docker-compose.yml

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gestao_turnos
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      args:
        # ✅ Passar UID/GID do usuário do host
        USER_ID: ${USER_ID:-1000}
        GROUP_ID: ${GROUP_ID:-1000}
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/gestao_turnos
    volumes:
      # ✅ Bind mount do código
      - ./app:/app/app:rw
      - ./migrations:/app/migrations:rw
      # ✅ Criar pasta migrations se não existir
    ports:
      - "8000:8000"
    command: python -m app.run_all

volumes:
  postgres_data:
```

### 3. Criar .env com Seu UID/GID

```bash
# .env

# Detectar automaticamente seu UID/GID
USER_ID=$(id -u)
GROUP_ID=$(id -g)

# Ou manualmente (linux)
USER_ID=1000
GROUP_ID=1000

# Resto das variáveis
APP_TIMEZONE=Europe/Lisbon
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/gestao_turnos
TELEGRAM_BOT_TOKEN=seu_token_aqui
# ...
```

### 4. Script Helper para Detectar UID/GID Automaticamente

```bash
#!/bin/bash
# scripts/set_env.sh

# Detectar UID/GID do usuário atual
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

echo "Usando USER_ID=$USER_ID GROUP_ID=$GROUP_ID"

# Executar docker compose com essas variáveis
docker compose "$@"
```

```bash
# Tornar executável
chmod +x scripts/set_env.sh

# Usar:
./scripts/set_env.sh up -d --build
./scripts/set_env.sh down
./scripts/set_env.sh logs -f
```

### 5. Comandos Alembic no Docker

```bash
# Inicializar Alembic (primeira vez)
docker compose exec app alembic init migrations

# Criar migration automática
docker compose exec app alembic revision --autogenerate -m "nome_da_migration"

# Aplicar migrations
docker compose exec app alembic upgrade head

# Rollback
docker compose exec app alembic downgrade -1

# Ver histórico
docker compose exec app alembic history

# Ver status atual
docker compose exec app alembic current
```

### 6. Estrutura de Pastas (com Permissões Corretas)

```bash
gestao_turnos/
├── app/                    # UID:GID do host
│   ├── __init__.py
│   ├── main.py
│   └── ...
├── migrations/             # ✅ Criado pelo container = seu UID:GID
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_xxx.py
├── docker-compose.yml
├── Dockerfile
└── .env
```

### 7. Verificar Permissões

```bash
# Listar permissões
ls -la migrations/

# Deve mostrar:
# drwxr-xr-x  leonardo leonardo  migrations/
# -rw-r--r--  leonardo leonardo  migrations/env.py
# -rw-r--r--  leonardo leonardo  migrations/versions/001_xxx.py

# ✅ Está com seu usuário? Perfeito!
```

---

## 🚀 Workflow Completo

### Setup Inicial (Uma Vez)

```bash
# 1. Criar arquivo .env com UID/GID
cat >> .env << EOF
USER_ID=$(id -u)
GROUP_ID=$(id -g)
EOF

# 2. Build containers
docker compose up -d --build

# 3. Inicializar Alembic
docker compose exec app alembic init migrations

# 4. Editar migrations/env.py (no seu editor local!)
# - Adicionar import dos models
# - Configurar target_metadata

# 5. Criar primeira migration
docker compose exec app alembic revision --autogenerate -m "initial schema"

# 6. Aplicar
docker compose exec app alembic upgrade head
```

### Workflow Diário

```bash
# Editar models.py no seu editor local
# Criar migration
docker compose exec app alembic revision --autogenerate -m "add campo X"

# Aplicar
docker compose exec app alembic upgrade head

# Se der erro, rollback
docker compose exec app alembic downgrade -1

# Editar arquivo de migration manualmente (no host!)
# Aplicar novamente
docker compose exec app alembic upgrade head
```

---

## 🔧 Alternativa: Makefile para Facilitar

```makefile
# Makefile

.PHONY: help build up down logs shell alembic-init alembic-migrate alembic-upgrade alembic-downgrade

# Detectar UID/GID
export USER_ID := $(shell id -u)
export GROUP_ID := $(shell id -g)

help:
	@echo "Comandos disponíveis:"
	@echo "  make build          - Build containers"
	@echo "  make up             - Start containers"
	@echo "  make down           - Stop containers"
	@echo "  make logs           - Ver logs"
	@echo "  make shell          - Shell no container"
	@echo "  make alembic-init   - Inicializar Alembic"
	@echo "  make alembic-migrate MSG='mensagem' - Criar migration"
	@echo "  make alembic-upgrade - Aplicar migrations"
	@echo "  make alembic-downgrade - Rollback migration"

build:
	docker compose build --build-arg USER_ID=$(USER_ID) --build-arg GROUP_ID=$(GROUP_ID)

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec app bash

alembic-init:
	docker compose exec app alembic init migrations
	@echo "✅ Alembic inicializado! Edite migrations/env.py"

alembic-migrate:
	@if [ -z "$(MSG)" ]; then echo "❌ Use: make migrate MSG='mensagem'"; exit 1; fi
	docker compose exec app alembic revision --autogenerate -m "$(MSG)"

alembic-upgrade:
	docker compose exec app alembic upgrade head

alembic-downgrade:
	docker compose exec app alembic downgrade -1

# Comandos combinados
restart: down up

rebuild: down build up
```

**Uso:**

```bash
# Build e subir
make build
make up

# Criar migration
make alembic-migrate MSG="add subscription fields"

# Aplicar
make alembic-upgrade

# Ver logs
make logs

# Shell no container
make shell
```

---

## 🐛 Troubleshooting

### Problema: Arquivos ainda são criados como root

```bash
# Verificar se build args foram passados
docker compose config

# Deve mostrar:
# services:
#   app:
#     build:
#       args:
#         USER_ID: "1000"
#         GROUP_ID: "1000"
```

**Solução:**
```bash
# Forçar rebuild
docker compose build --no-cache --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)
```

### Problema: Permission denied ao criar migration

```bash
# Verificar UID dentro do container
docker compose exec app id

# Deve mostrar:
# uid=1000(appuser) gid=1000(appuser)
```

**Solução:**
```bash
# Recriar pasta migrations com permissões corretas
sudo rm -rf migrations
mkdir migrations
docker compose exec app alembic init migrations
```

### Problema: Container não inicia após trocar USER

```bash
# Ver logs
docker compose logs app

# Erro comum: "permission denied: /app/something"
```

**Solução:**
```bash
# No Dockerfile, garantir que appuser tem ownership
RUN chown -R appuser:appuser /app
```

---

## ✅ Verificação Final

```bash
# 1. Criar migration
docker compose exec app alembic revision --autogenerate -m "test"

# 2. Verificar permissões
ls -la migrations/versions/

# ✅ Deve mostrar SEU usuário, não root!

# 3. Editar arquivo (deve funcionar sem sudo)
nano migrations/versions/001_test.py

# 4. Aplicar
docker compose exec app alembic upgrade head

# 5. Success! 🎉
```

---

## 📝 Resumo

**Antes:**
```bash
❌ docker compose exec app alembic revision ...
❌ Permission denied ao editar migrations/versions/001_xxx.py
❌ Precisa usar sudo (péssima ideia)
```

**Depois:**
```bash
✅ docker compose exec app alembic revision ...
✅ Editar migrations/versions/001_xxx.py normalmente
✅ Tudo funciona como esperado!
```

**Chave do Sucesso:**
1. Dockerfile com ARG USER_ID/GROUP_ID
2. docker-compose.yml passa UID/GID do host
3. Container roda como appuser (não root)
4. Arquivos criados = seu UID/GID = editáveis no host

🎯 **Zero problemas de permissão!**
