import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

@pytest.fixture
def db_engine():
    """Engine do banco de dados."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Sessão do banco de dados."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def db_session_rls():
    """
    Sessão do banco de dados que respeita RLS.
    Cria um role temporário sem BYPASSRLS para testar políticas.
    """
    # Conectar como superuser para criar o role temporário
    superuser_engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/gestao_turnos")
    
    with superuser_engine.connect() as conn:
        # Criar role sem bypass RLS se não existir
        conn.execute(text("""
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
        conn.commit()
    superuser_engine.dispose()
    
    # Conectar como role sem bypass
    rls_engine = create_engine("postgresql+psycopg://test_rls_user:test123@postgres:5432/gestao_turnos")
    Session = sessionmaker(bind=rls_engine)
    session = Session()
    
    yield session
    
    session.close()
    rls_engine.dispose()
