import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.config import get_settings
from app.main import app

@pytest.fixture
def client():
    """TestClient para FastAPI."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """AsyncClient para FastAPI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_engine():
    """Engine do banco de dados (async)."""
    settings = get_settings()
    # Force use of psycopg driver for tests if not set
    url = settings.database_url
    if not url:
        # Default to Docker service URL if not set in .env
        url = "postgresql+psycopg://postgres:postgres@localhost:5432/gestao_turnos"
        
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://")
        
    engine = create_async_engine(url)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Sessão do banco de dados (async)."""
    Session = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

@pytest.fixture
async def db_session_rls():
    """
    Sessão do banco de dados que respeita RLS (async).
    Cria um role temporário sem BYPASSRLS para testar políticas.
    """
    settings = get_settings()
    url = settings.database_url
    if not url:
        url = "postgresql+psycopg://postgres:postgres@localhost:5432/gestao_turnos"
        
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://")

    # Conectar como superuser para criar o role temporário
    superuser_engine = create_async_engine(url)
    
    async with superuser_engine.begin() as conn:
        # Criar role sem bypass RLS se não existir
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_rls_user') THEN
                    CREATE ROLE test_rls_user LOGIN PASSWORD 'test123';
                    GRANT CONNECT ON DATABASE gestao_turnos TO test_rls_user;
                    GRANT USAGE ON SCHEMA public TO test_rls_user;
                    GRANT ALL ON ALL TABLES IN SCHEMA public TO test_rls_user;
                    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO test_rls_user;
                END IF;
            END $$;
        """))
    await superuser_engine.dispose()
    
    # Conectar como role sem bypass
    # Construir URL do usuário RLS baseado na URL original
    u = make_url(url)
    rls_url_obj = u.set(username="test_rls_user", password="test123")
    rls_engine = create_async_engine(rls_url_obj)
    
    Session = async_sessionmaker(bind=rls_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        yield session
        
    await rls_engine.dispose()
