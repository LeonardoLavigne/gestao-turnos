# Makefile para gestão de turnos

.PHONY: help build up down restart logs shell alembic-init alembic-migrate alembic-upgrade alembic-downgrade alembic-history

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
	@echo "  make shell              - Shell no container"
	@echo ""
	@echo "Alembic (Migrations):"
	@echo "  make alembic-init       - Inicializar Alembic (primeira vez)"
	@echo "  make alembic-migrate MSG='msg' - Criar nova migration"
	@echo "  make alembic-upgrade    - Aplicar todas migrations"
	@echo "  make alembic-downgrade  - Rollback última migration"
	@echo "  make alembic-history    - Ver histórico de migrations"
	@echo ""
	@echo "Atalhos:"
	@echo "  make rebuild            - Down + Build + Up"
	@echo "  make fresh              - Down + Clean volumes + Build + Up"
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
	docker compose down

restart: down up ## Restart containers

logs: ## Ver logs (follow)
	docker compose logs -f

shell: ## Shell no container
	docker compose exec gestao-turnos bash

# Comandos Alembic
alembic-init: ## Inicializar Alembic (primeira vez)
	@echo "🔧 Inicializando Alembic..."
	@mkdir -p migrations
	docker compose exec gestao-turnos uv run alembic init migrations
	@echo "✅ Alembic inicializado!"
	@echo "⚠️  Edite migrations/env.py para configurar target_metadata"

alembic-migrate: ## Criar migration (uso: make alembic-migrate MSG='nome da migration')
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Erro: Use 'make alembic-migrate MSG=\"mensagem\"'"; \
		exit 1; \
	fi
	@echo "📝 Criando migration: $(MSG)..."
	docker compose exec gestao-turnos uv run alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration criada! Revise o arquivo antes de aplicar."

alembic-upgrade: ## Aplicar migrations
	@echo "⬆️  Aplicando migrations..."
	docker compose exec gestao-turnos uv run alembic upgrade head
	@echo "✅ Migrations aplicadas!"

alembic-downgrade: ## Rollback última migration
	@echo "⬇️  Fazendo rollback..."
	docker compose exec gestao-turnos uv run alembic downgrade -1
	@echo "✅ Rollback concluído!"

alembic-history: ## Ver histórico de migrations
	docker compose exec gestao-turnos uv run alembic history

alembic-current: ## Ver migration atual
	docker compose exec gestao-turnos uv run alembic current

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

# Verificar permissões
check-permissions: ## Verificar permissões das pastas
	@echo "📁 Verificando permissões..."
	@ls -la migrations/ 2>/dev/null || echo "⚠️  Pasta migrations/ não existe"
	@ls -la data/ 2>/dev/null || echo "⚠️  Pasta data/ não existe"

# Comandos locais com uv (sem Docker)
dev: ## Rodar app localmente com uv
	uv run python -m app.run_all

test: ## Rodar testes com uv
	uv run pytest tests/ -v

lint: ## Lint com ruff
	uv run ruff check app/

format: ## Format com ruff
	uv run ruff format app/

add: ## Adicionar dependência (uso: make add PKG=nome_do_pacote)
	@if [ -z "$(PKG)" ]; then \
		echo "❌ Erro: Use 'make add PKG=nome_do_pacote'"; \
		exit 1; \
	fi
	uv add $(PKG)

sync: ## Sincronizar ambiente virtual
	uv sync
