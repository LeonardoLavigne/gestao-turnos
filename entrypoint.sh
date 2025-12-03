#!/bin/bash
set -e

echo "🔄 Aguardando PostgreSQL estar pronto..."
sleep 2

# Aplicar migrations automaticamente
if [ -f "alembic.ini" ]; then
    echo "🔄 Aplicando migrations..."
    uv run alembic upgrade head
    echo "✅ Migrations aplicadas com sucesso!"
else
    echo "⚠️  alembic.ini não encontrado, pulando migrations..."
fi

echo "🚀 Iniciando aplicação..."
exec uv run python -m app.run_all
