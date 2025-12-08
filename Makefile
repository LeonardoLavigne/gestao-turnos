# Makefile para gestão de turnos (Backend + Bot)

.PHONY: help build up down restart logs shell-backend shell-bot alembic-init alembic-migrate \
        alembic-upgrade alembic-downgrade alembic-history alembic-current \
        rebuild fresh check-permissions test-backend test-bot

# ✅ Detectar UID/GID automaticamente
export USER_ID := $(shell id -u)
export GROUP_ID := $(shell id -g)

help: ## Mostrar ajuda
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "  make build              - Build containers com UID/GID correto"
	@echo "  make up                 - Start containers"
	@echo "  make down               - Stop containers"
	@echo "  make restart            - Restart containers"
	@echo "  make logs               - Ver logs (follow)"
	@echo "  make shell-backend      - Shell no container backend"
	@echo "  make shell-bot          - Shell no container bot"
	@echo ""
	@echo "Alembic (Migrations - rodadas no backend):"
	@echo "  make alembic-init       - Inicializar Alembic (primeira vez)"
	@echo "  make alembic-migrate MSG='msg' - Criar nova migration"
	@echo "  make alembic-upgrade    - Aplicar todas migrations"
	@echo "  make alembic-downgrade  - Rollback última migration"
	@echo "  make alembic-history    - Ver histórico de migrations"
	@echo ""
	@echo "Testes:"
	@echo "  make test-backend       - Rodar testes do backend"
	@echo "  make test-bot           - Rodar testes do bot"
	@echo "  make test-backend-cov   - Rodar testes do backend com cobertura"
	@echo "  make test-bot-cov       - Rodar testes do bot com cobertura"
	@echo ""
	@echo "ℹ️  Usando USER_ID=$(USER_ID) GROUP_ID=$(GROUP_ID)"

build: ## Build containers
	@echo "🔨 Building com USER_ID=$(USER_ID) GROUP_ID=$(GROUP_ID)..."
	docker compose build --build-arg USER_ID=$(USER_ID) --build-arg GROUP_ID=$(GROUP_ID)

up: ## Start containers
	@echo "🚀 Starting containers..."
	docker compose up -d

down: ## Stop containers
	@echo "🛑 Stopping containers..."
	docker compose down --remove-orphans

restart: down up ## Restart containers

logs: ## Ver logs (follow)
	docker compose logs -f

shell-backend: ## Shell no container backend
	docker compose exec backend bash

shell-bot: ## Shell no container bot
	docker compose exec bot bash

# Comandos Alembic (Backend)
alembic-init: ## Inicializar Alembic (primeira vez)
	@echo "🔧 Inicializando Alembic..."
	docker compose exec backend uv run alembic init migrations
	@echo "✅ Alembic inicializado!"

alembic-migrate: ## Criar migration (uso: make alembic-migrate MSG='nome da migration')
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Erro: Use 'make alembic-migrate MSG=\"mensagem\"'"; \
		exit 1; \
	fi
	@echo "📝 Criando migration: $(MSG)..."
	docker compose exec backend uv run alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration criada! Revise o arquivo antes de aplicar."

alembic-upgrade: ## Aplicar migrations
	@echo "⬆️  Aplicando migrations..."
	docker compose exec backend uv run alembic upgrade head
	@echo "✅ Migrations aplicadas!"

alembic-downgrade: ## Rollback última migration
	@echo "⬇️  Fazendo rollback..."
	docker compose exec backend uv run alembic downgrade -1
	@echo "✅ Rollback concluído!"

alembic-history: ## Ver histórico de migrations
	docker compose exec backend uv run alembic history

alembic-current: ## Ver migration atual
	docker compose exec backend uv run alembic current

# Testes
# Testes
test-backend: ## Rodar testes do backend
	docker compose exec backend uv run pytest tests/ -v

test-backend-cov: ## Rodar testes do backend com cobertura
	docker compose exec backend uv run pytest tests/ -v --cov=app --cov-report=term-missing

test-bot: ## Rodar testes do bot
	docker compose exec bot uv run pytest tests/ -v

test-bot-cov: ## Rodar testes do bot com cobertura
	docker compose exec bot uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Atalhos úteis
rebuild: down build up ## Down + Build + Up

fresh: down ## Down + Clean volumes + Build + Up
	@echo "🗑️  Removendo volumes..."
	docker compose down -v
	@echo "🔨 Rebuilding..."
	$(MAKE) build
	@echo "🚀 Starting..."
	$(MAKE) up
	@echo "✅ Fresh start completo!"

# Verificar permissões (Adaptação para nova estrutura)
check-permissions: ## Verificar permissões das pastas
	@echo "📁 Verificando permissões..."
	@ls -la backend/migrations/ 2>/dev/null || echo "⚠️  Pasta backend/migrations/ não existe"
	@ls -la backend/data/ 2>/dev/null || echo "⚠️  Pasta backend/data/ não existe"

