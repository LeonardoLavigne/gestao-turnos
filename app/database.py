from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    """
    Retorna URL do banco de dados.
    Prioridade: DATABASE_URL (PostgreSQL) > SQLite
    """
    settings = get_settings()
    
    # Se DATABASE_URL está definida, usar (PostgreSQL)
    if settings.database_url:
        return settings.database_url
    
    # Fallback para SQLite
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def _create_engine():
    """
    Cria engine com configuração apropriada para o banco.
    """
    database_url = _get_database_url()
    
    # Configuração base
    engine_kwargs = {}
    
    # Configurações específicas por tipo de banco
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    
    elif database_url.startswith("postgresql"):
        # ✅ Connection pooling para PostgreSQL
        engine_kwargs.update({
            "pool_size": 10,          # Connections simultâneas base
            "max_overflow": 20,       # Pool elástico em picos
            "pool_pre_ping": True,    # Testar connection antes de usar
            "pool_recycle": 3600,     # Reciclar após 1h
            "pool_timeout": 30,       # Timeout para pegar connection
        })
    
    return create_engine(database_url, **engine_kwargs)


# ✅ Criar engine com configuração apropriada
engine = _create_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
