#!/bin/bash
set -e


echo "🔄 Aguardando PostgreSQL estar pronto..."
# Aguardar PostgreSQL com pg_isready para maior confiabilidade
until pg_isready -h postgres -U postgres -d gestao_turnos > /dev/null 2>&1; do
    echo "⏳ PostgreSQL ainda não está pronto, aguardando..."
    sleep 1
done
echo "✅ PostgreSQL está pronto!"


# Aplicar migrations automaticamente
if [ -f "alembic.ini" ]; then
    echo "🔄 Aplicando migrations..."
    uv run alembic upgrade head
    echo "✅ Migrations aplicadas com sucesso!"
else
    echo "⚠️  alembic.ini não encontrado, pulando migrations..."
fi

if [ $# -eq 0 ]; then
    echo "🚀 Iniciando aplicação..."
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "🔧 Executando comando customizado: $@"
    exec "$@"
fi
