from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    """
    Retorna URL do banco de dados para Async.
    Prioridade: DATABASE_URL (PostgreSQL) > SQLite
    """
    settings = get_settings()
    
    # Se DATABASE_URL está definida, usar (PostgreSQL)
    if settings.database_url:
        # Garantir driver async se não especificado
        if settings.database_url.startswith("postgresql://"):
             return settings.database_url.replace("postgresql://", "postgresql+psycopg://")
        return settings.database_url
    
    # Fallback para SQLite (apenas se tiver aiosqlite, senao vai falhar na criação do engine async)
    # Como não adicionamos aiosqlite, assumiremos que o ambiente de dev/prod usa postgres
    # Mas para garantir robustez, deixaremos o path aqui caso o user instale aiosqlite depois
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def _create_engine():
    """
    Cria engine async com configuração apropriada para o banco.
    """
    database_url = _get_database_url()
    
    # Configuração base
    engine_kwargs = {}
    
    # Configurações específicas por tipo de banco
    if "sqlite" in database_url:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    
    elif "postgresql" in database_url:
        # ✅ Connection pooling para PostgreSQL
        engine_kwargs.update({
            "pool_size": 10,          # Connections simultâneas base
            "max_overflow": 20,       # Pool elástico em picos
            "pool_pre_ping": True,    # Testar connection antes de usar
            "pool_recycle": 3600,     # Reciclar após 1h
            "pool_timeout": 30,       # Timeout para pegar connection
        })
    
    return create_async_engine(database_url, **engine_kwargs)


def _is_postgresql() -> bool:
    """Verifica se está usando PostgreSQL."""
    return "postgresql" in _get_database_url()


# ✅ Criar engine async com configuração apropriada
engine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db(request: Request = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para FastAPI que fornece sessão assíncrona do banco de dados.
    
    Se request.state.telegram_user_id estiver definido (via RLSMiddleware),
    configura SET LOCAL app.current_user_id para RLS funcionar corretamente.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Configurar RLS se telegram_user_id estiver disponível
            if request is not None and _is_postgresql():
                user_id = getattr(request.state, "telegram_user_id", None)
                if user_id is not None:
                    await db.execute(
                        text("SELECT set_config('app.current_user_id', :user_id, true)"),
                        {"user_id": str(user_id)}
                    )
            yield db
        finally:
            await db.close()
